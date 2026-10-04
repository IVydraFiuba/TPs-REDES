import pytest

from lib.capas.rdt.implementaciones.stopwait import CanalStopWait
from lib.capas.rdt.segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)
from lib.capas.udp.errores import ErrorComunicacion, ErrorTiempoEspera
from lib.constantes import (
    MAX_REINTENTOS_SW,
    RTO_MINIMO_SW,
    RTO_SW,
)

# Marca una espera que vence sin que llegue nada.
TIMEOUT = object()


class EnlaceFalso:
    """Entrega las respuestas en orden; sin más, vence el timeout."""

    def __init__(self, respuestas=None):
        self.enviados = []
        self.recibidos = list(respuestas or [])
        self.timeouts_pedidos = []

    def enviar(self, datos):
        self.enviados.append(datos)

    def recibir(self, timeout=None):
        self.timeouts_pedidos.append(timeout)
        if not self.recibidos or self.recibidos[0] is TIMEOUT:
            if self.recibidos:
                self.recibidos.pop(0)
            raise ErrorTiempoEspera("sin datos")
        return self.recibidos.pop(0)


def ack(confirmacion):
    return codificar_segmento(Segmento(
        TipoSegmento.ACK,
        confirmacion=confirmacion,
    ))


def datos(secuencia, carga):
    return codificar_segmento(Segmento(
        TipoSegmento.DATOS,
        secuencia=secuencia,
        carga=carga,
    ))


def enviados_de_tipo(enlace, tipo):
    return [
        decodificar_segmento(datagrama)
        for datagrama in enlace.enviados
        if decodificar_segmento(datagrama).tipo == tipo
    ]


# ------------------------------------------------------------- emisión


def test_enviar_vuelve_cuando_llega_la_confirmacion():
    enlace = EnlaceFalso([ack(1)])
    canal = CanalStopWait(enlace)

    canal.enviar(b"hola")

    assert len(enlace.enviados) == 1
    segmento = decodificar_segmento(enlace.enviados[0])
    assert segmento.tipo == TipoSegmento.DATOS
    assert segmento.secuencia == 0
    assert segmento.carga == b"hola"
    assert canal.secuencia_actual_envio == 1


def test_un_ack_viejo_no_provoca_retransmision():
    # confirmacion=0 significa "sigo esperando el 0": no confirma nada.
    enlace = EnlaceFalso([ack(0), ack(1)])
    canal = CanalStopWait(enlace)

    canal.enviar(b"hola")

    assert len(enlace.enviados) == 1


def test_recibir_datos_mientras_espera_no_retransmite():
    enlace = EnlaceFalso([datos(0, b"X"), ack(1)])
    canal = CanalStopWait(enlace)

    canal.enviar(b"hola")

    assert len(enviados_de_tipo(enlace, TipoSegmento.DATOS)) == 1
    # El segmento entrante quedó guardado y se entrega después.
    assert canal.recibir() == b"X"


def test_el_timeout_retransmite_el_mismo_segmento():
    enlace = EnlaceFalso([TIMEOUT, ack(1)])
    canal = CanalStopWait(enlace)

    canal.enviar(b"hola")

    assert len(enlace.enviados) == 2
    assert enlace.enviados[0] == enlace.enviados[1]


def test_el_rto_se_duplica_con_cada_timeout():
    enlace = EnlaceFalso([TIMEOUT, TIMEOUT, ack(1)])
    canal = CanalStopWait(enlace)

    canal.enviar(b"hola")

    assert enlace.timeouts_pedidos == [RTO_SW, RTO_SW * 2, RTO_SW * 4]
    # Regla de Karn: el ACK de un segmento retransmitido no sirve como
    # muestra de RTT, asi que el backoff se mantiene.
    assert canal._rto == RTO_SW * 4


def test_el_rto_se_ajusta_al_rtt_medido():
    # El enlace falso contesta al instante: el RTT medido es casi cero y
    # el estimador queda apoyado contra el piso.
    enlace = EnlaceFalso([ack(1), ack(2)])
    canal = CanalStopWait(enlace)

    canal.enviar(b"uno")

    assert canal._rto == RTO_MINIMO_SW
    assert canal._srtt is not None

    canal.enviar(b"dos")

    # La segunda espera ya usa el RTO estimado, no el inicial.
    assert enlace.timeouts_pedidos == [RTO_SW, RTO_MINIMO_SW]


def test_un_segmento_limpio_despues_de_un_backoff_baja_el_rto():
    enlace = EnlaceFalso([TIMEOUT, ack(1), ack(2)])
    canal = CanalStopWait(enlace)

    canal.enviar(b"uno")
    assert canal._rto == RTO_SW * 2

    canal.enviar(b"dos")
    assert canal._rto == RTO_MINIMO_SW


def test_enviar_corta_tras_agotar_los_reintentos():
    enlace = EnlaceFalso()
    canal = CanalStopWait(enlace)

    with pytest.raises(ErrorComunicacion):
        canal.enviar(b"hola")

    assert len(enlace.enviados) == MAX_REINTENTOS_SW + 1


# ------------------------------------------------------------ recepción


def test_recibir_entrega_en_orden_y_confirma_el_proximo():
    enlace = EnlaceFalso([datos(0, b"A")])
    canal = CanalStopWait(enlace)

    assert canal.recibir() == b"A"

    confirmacion = decodificar_segmento(enlace.enviados[0])
    assert confirmacion.tipo == TipoSegmento.ACK
    assert confirmacion.confirmacion == 1


def test_un_duplicado_se_reconfirma_y_no_se_entrega_dos_veces():
    enlace = EnlaceFalso([datos(0, b"A"), datos(0, b"A"), datos(1, b"B")])
    canal = CanalStopWait(enlace)

    assert canal.recibir() == b"A"
    assert canal.recibir() == b"B"

    confirmaciones = [
        segmento.confirmacion
        for segmento in enviados_de_tipo(enlace, TipoSegmento.ACK)
    ]
    # El duplicado se vuelve a confirmar con el mismo valor, para que el
    # emisor deje de reenviarlo.
    assert confirmaciones == [1, 1, 2]


def test_recibir_ignora_los_ack_sueltos():
    enlace = EnlaceFalso([ack(5), datos(0, b"A")])
    canal = CanalStopWait(enlace)

    assert canal.recibir() == b"A"


def test_recibir_corta_si_el_par_deja_de_enviar():
    enlace = EnlaceFalso()
    canal = CanalStopWait(enlace)

    with pytest.raises(ErrorComunicacion):
        canal.recibir()


def test_cerrar_responde_los_rezagados():
    enlace = EnlaceFalso([datos(0, b"A"), datos(0, b"A")])
    canal = CanalStopWait(enlace)

    assert canal.recibir() == b"A"
    enlace.enviados.clear()

    canal.cerrar()

    # El duplicado que llego tarde se vuelve a confirmar. Si el canal
    # cerrara en el acto, el par seguiria retransmitiendo contra nadie.
    confirmaciones = enviados_de_tipo(enlace, TipoSegmento.ACK)
    assert len(confirmaciones) == 1
    assert confirmaciones[0].confirmacion == 1
