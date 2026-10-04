import time

import pytest

from lib.capas.rdt.implementaciones import sack as modulo_sack
from lib.capas.rdt.implementaciones.sack import CanalSack
from lib.capas.rdt.sack_utiles import (
    codificar_sack,
    decodificar_sack,
)
from lib.capas.rdt.segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)
from lib.capas.udp.errores import ErrorComunicacion, ErrorTiempoEspera
from lib.constantes import (
    RTO_MAXIMO_SACK,
    RTO_MINIMO_SACK,
    VENTANA_SACK,
)


class EnlaceFalso:
    def __init__(self):
        self.recibidos = []
        self.enviados = []

    def enviar(self, datos):
        self.enviados.append(datos)

    def recibir(self, timeout=None):
        if not self.recibidos:
            raise ErrorTiempoEspera("sin datos")
        return self.recibidos.pop(0)


def test_enviar_asigna_secuencias_consecutivas():
    """Verifica que cada segmento enviado tenga una secuencia consecutiva."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    canal.enviar(b"A" * 100)
    canal.enviar(b"B" * 200)
    canal.enviar(b"C" * 300)

    segmentos = [
        decodificar_segmento(datos)
        for datos in enlace.enviados
    ]

    assert [segmento.secuencia for segmento in segmentos] == [0, 1, 2]
    assert [len(segmento.carga) for segmento in segmentos] == [
        100, 200, 300
    ]


def test_recibir_envia_ack_con_siguiente_secuencia():
    """Verifica que al recibir un segmento se envíe el ACK correcto."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    segmento = Segmento(
        tipo=TipoSegmento.DATOS,
        secuencia=0,
        carga=b"A",
    )

    enlace.recibidos.append(codificar_segmento(segmento))

    assert canal.recibir() == b"A"

    ack = decodificar_segmento(enlace.enviados[0])

    assert ack.tipo == TipoSegmento.ACK
    assert ack.confirmacion == 1


def test_ack_acumulativo_y_sack_elimina_secuencias_confirmadas():
    """Verifica que ACK y SACK eliminen secuencias de los pendientes."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    for dato in [b"A", b"B", b"C", b"D"]:
        canal.enviar(dato)

    ack = Segmento(
        tipo=TipoSegmento.ACK,
        confirmacion=2,
        carga=codificar_sack([(3, 3)]),
    )

    enlace.recibidos.append(codificar_segmento(ack))

    canal._recibir_ack()

    # Solo la secuencia 2 queda pendiente de confirmación.
    assert list(canal._pendientes.keys()) == [2]
    assert set(canal._tiempos_pendientes) == {2}


def test_recibir_fuera_de_orden_envia_ack_sack():
    """Verifica que un segmento fuera de orden genere un ACK Sack."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    canal._proxima_secuencia_recibir = 1

    enlace.recibidos.append(
        codificar_segmento(
            Segmento(
                TipoSegmento.DATOS,
                secuencia=2,
                carga=b"C",
            )
        )
    )

    enlace.recibidos.append(
        codificar_segmento(
            Segmento(
                TipoSegmento.DATOS,
                secuencia=1,
                carga=b"B",
            )
        )
    )

    assert canal.recibir() == b"B"

    ack = decodificar_segmento(enlace.enviados[0])

    assert ack.confirmacion == 1
    assert decodificar_sack(ack.carga) == [(2, 2)]

    assert canal.recibir() == b"C"


def test_retransmite_segmento_cuando_vence_timeout():
    """Verifica que se retransmita un segmento cuyo RTO se venció."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    canal.enviar(b"A")
    canal.enviar(b"B")
    canal.enviar(b"C")

    assert len(enlace.enviados) == 3

    ack = Segmento(
        tipo=TipoSegmento.ACK,
        confirmacion=1,
        carga=codificar_sack([(2, 2)]),
    )

    canal._procesar_ack(ack)

    assert list(canal._pendientes.keys()) == [1]

    # Despues del ACK el estimador fija el RTO; se fuerza uno minusculo
    # para que el pendiente venza sin esperar.
    canal._rto = 0.01
    time.sleep(0.02)

    enlace.enviados.clear()

    canal._retransmitir_vencidos()

    assert len(enlace.enviados) == 1

    segmento = decodificar_segmento(enlace.enviados[0])

    assert segmento.secuencia == 1


def test_recibir_fuera_de_orden_entrega_en_orden():
    """Verifica que los segmentos fuera de orden se almacenen en buffer."""

    def segmento(seq, dato):
        return codificar_segmento(
            Segmento(
                TipoSegmento.DATOS,
                secuencia=seq,
                carga=dato,
            )
        )

    enlace = EnlaceFalso()
    enlace.recibidos = [
        segmento(0, b"A"),
        segmento(1, b"B"),
        segmento(3, b"D"),
        segmento(4, b"E"),
        segmento(2, b"C"),
    ]

    canal = CanalSack(enlace)

    assert canal.recibir() == b"A"
    assert canal.recibir() == b"B"

    # 3 y 4 llegan antes que 2 y quedan almacenados.
    assert canal.recibir() == b"C"

    # Al llegar 2, los segmentos almacenados salen del buffer en orden.
    assert canal.recibir() == b"D"
    assert canal.recibir() == b"E"

    assert canal._recibidos == {}
    assert canal._proxima_secuencia_recibir == 5


def test_vaciar_espera_confirmaciones():
    """Verifica que vaciar espere hasta confirmar todos los segmentos."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    canal.enviar(b"A")

    ack = Segmento(
        tipo=TipoSegmento.ACK,
        confirmacion=1,
    )

    enlace.recibidos.append(codificar_segmento(ack))

    canal.vaciar()

    assert canal._pendientes == {}


def _datos(secuencia, carga):
    return codificar_segmento(Segmento(
        TipoSegmento.DATOS,
        secuencia=secuencia,
        carga=carga,
    ))


def test_un_duplicado_ya_entregado_no_vuelve_al_buffer():
    """Un DATOS por debajo del acumulativo se descarta, no se guarda."""
    enlace = EnlaceFalso()
    enlace.recibidos = [
        _datos(0, b"A"),
        _datos(0, b"A"),
        _datos(1, b"B"),
    ]

    canal = CanalSack(enlace)

    assert canal.recibir() == b"A"
    assert canal.recibir() == b"B"

    # Si el duplicado se hubiera guardado, quedaria ahi para siempre y
    # ademas lo reportarian todos los ACK siguientes como un rango.
    assert canal._recibidos == {}

    ultimo = decodificar_segmento(enlace.enviados[-1])
    assert decodificar_sack(ultimo.carga) == []


def test_la_ventana_frena_al_emisor_cuando_se_llena():
    """Con la ventana llena y sin ACKs, no sale ningun segmento nuevo."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    for _ in range(VENTANA_SACK):
        canal.enviar(b"X")

    assert len(enlace.enviados) == VENTANA_SACK

    with pytest.raises(ErrorComunicacion):
        canal.enviar(b"X")

    secuencias = {
        decodificar_segmento(datagrama).secuencia
        for datagrama in enlace.enviados
    }
    assert secuencias == set(range(VENTANA_SACK))


def test_vaciar_corta_si_el_par_deja_de_confirmar():
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    canal.enviar(b"A")

    with pytest.raises(ErrorComunicacion):
        canal.vaciar()

    assert canal._rto == RTO_MAXIMO_SACK


def test_cerrar_responde_los_rezagados():
    enlace = EnlaceFalso()
    enlace.recibidos = [_datos(0, b"A"), _datos(0, b"A")]

    canal = CanalSack(enlace)

    assert canal.recibir() == b"A"
    enlace.enviados.clear()

    canal.cerrar()

    assert len(enlace.enviados) == 1
    ack = decodificar_segmento(enlace.enviados[0])
    assert ack.tipo == TipoSegmento.ACK
    assert ack.confirmacion == 1


def test_el_rto_se_ajusta_al_rtt_medido():
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    canal.enviar(b"A")
    enlace.recibidos = [codificar_segmento(
        Segmento(TipoSegmento.ACK, confirmacion=1))]

    canal.vaciar()

    # El enlace falso contesta al instante: el estimador queda contra
    # el piso, muy por debajo del RTO_SACK inicial de 1 segundo.
    assert canal._rto == RTO_MINIMO_SACK
    assert canal._srtt is not None


def test_un_segmento_retransmitido_no_sirve_como_muestra():
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    canal.enviar(b"A")
    canal._rto = 0.0
    canal._retransmitir_vencidos()

    enlace.recibidos = [codificar_segmento(
        Segmento(TipoSegmento.ACK, confirmacion=1))]
    canal._recibir_ack()

    # Regla de Karn: no se sabe a cual de los dos envios responde
    # el ACK, asi que no se toma muestra.
    assert canal._srtt is None


# ------------------- DATOS que llegan mientras se espera un ACK


def datos_de(secuencia, carga=b"X"):
    return codificar_segmento(Segmento(
        tipo=TipoSegmento.DATOS,
        secuencia=secuencia,
        carga=carga,
    ))


def acks_enviados(enlace):
    return [
        decodificar_segmento(datos)
        for datos in enlace.enviados
        if decodificar_segmento(datos).tipo == TipoSegmento.ACK
    ]


def test_un_datos_que_llega_esperando_ack_se_confirma():
    """Descartarlo deja al par retransmitiendo hasta agotar reintentos."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)
    canal.enviar(b"mio")
    enlace.enviados.clear()

    # El par retransmite su propio segmento porque nuestro ACK se
    # perdio. Llega mientras estamos en vaciar(), esperando el ACK de lo
    # nuestro.
    enlace.recibidos.append(datos_de(0, b"suyo"))
    canal._esperar_progreso()

    confirmaciones = acks_enviados(enlace)
    assert len(confirmaciones) == 1
    assert decodificar_sack(confirmaciones[0].carga) == [(0, 0)]


def test_un_datos_recibido_esperando_ack_se_entrega_despues():
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)
    canal.enviar(b"mio")

    enlace.recibidos.append(datos_de(0, b"suyo"))
    canal._esperar_progreso()

    # Quedo guardado, no descartado: recibir() lo entrega sin que el par
    # tenga que volver a mandarlo.
    assert canal.recibir() == b"suyo"


def test_un_duplicado_esperando_ack_se_reconfirma_sin_guardarse():
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)
    enlace.recibidos.append(datos_de(0, b"suyo"))
    assert canal.recibir() == b"suyo"

    canal.enviar(b"mio")
    enlace.enviados.clear()

    # Ya lo entregamos; el par lo retransmite igual. Hay que reconfirmar
    # para que deje de hacerlo, pero no volver a guardarlo.
    enlace.recibidos.append(datos_de(0, b"suyo"))
    canal._esperar_progreso()

    confirmaciones = acks_enviados(enlace)
    assert len(confirmaciones) == 1
    assert confirmaciones[0].confirmacion == 1
    assert decodificar_sack(confirmaciones[0].carga) == []
    assert canal._recibidos == {}


def test_un_datos_entrante_no_agranda_el_rto():
    """El par esta vivo: agrandar el RTO seria lo contrario de lo util."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)
    canal.enviar(b"mio")
    rto_antes = canal._rto

    enlace.recibidos.append(datos_de(0, b"suyo"))
    canal._esperar_progreso()

    assert canal._rto == rto_antes
    assert canal._sin_progreso == 0


def test_recibir_corta_si_el_par_deja_de_enviar(monkeypatch):
    """Sin tope, el hilo de la sesion gira para siempre."""
    monkeypatch.setattr(modulo_sack, "ESPERA_RECEPCION_SACK", 0.0)
    canal = CanalSack(EnlaceFalso())

    with pytest.raises(ErrorComunicacion):
        canal.recibir()


def test_recibir_sigue_esperando_mientras_el_par_hable(monkeypatch):
    """Cada datagrama que llega renueva la paciencia."""
    monkeypatch.setattr(modulo_sack, "ESPERA_RECEPCION_SACK", 0.0)
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)

    # Un segmento fuera de orden no se puede entregar todavia, pero
    # prueba que el par esta vivo: no hay que cortar por eso.
    enlace.recibidos.append(datos_de(1, b"tarde"))
    enlace.recibidos.append(datos_de(0, b"temprano"))

    assert canal.recibir() == b"temprano"
    assert canal.recibir() == b"tarde"


def test_un_segmento_en_orden_se_confirma_una_sola_vez():
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)
    enlace.recibidos.append(datos_de(0, b"A"))

    assert canal.recibir() == b"A"

    confirmaciones = acks_enviados(enlace)
    assert len(confirmaciones) == 1
    assert confirmaciones[0].confirmacion == 1


# --------------------- orden entre retransmitir y agrandar el RTO


def test_el_timeout_retransmite_antes_de_agrandar_el_rto():
    """Si se agranda primero, el segmento no sale hasta la cuarta ronda.

    `_retransmitir_vencidos` compara el tiempo transcurrido contra
    `self._rto`. Duplicando el RTO en cada ronda, el umbral crece mas
    rapido que el reloj (1, 2, 4, 8) y el reenvio recien ocurre a los
    15 s de haber mandado el segmento.
    """
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)
    canal.enviar(b"mio")
    enlace.enviados.clear()

    # Una ronda sin nada que llegue: vence la espera.
    canal._esperar_progreso()

    reenviados = [
        decodificar_segmento(datos) for datos in enlace.enviados
    ]
    assert len(reenviados) == 1
    assert reenviados[0].secuencia == 0
    assert reenviados[0].carga == b"mio"


def test_el_timeout_retransmite_el_pendiente_mas_viejo():
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)
    canal.enviar(b"primero")
    canal.enviar(b"segundo")
    enlace.enviados.clear()

    canal._esperar_progreso()

    # Reenviar la ventana entera en cada timeout seria una tormenta de
    # 64 segmentos; alcanza con el mas antiguo sin confirmar.
    reenviados = [
        decodificar_segmento(datos) for datos in enlace.enviados
    ]
    assert [s.secuencia for s in reenviados] == [0]


def test_un_ack_que_libera_no_provoca_retransmision():
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)
    canal.enviar(b"mio")
    enlace.enviados.clear()
    enlace.recibidos.append(codificar_segmento(Segmento(
        tipo=TipoSegmento.ACK,
        confirmacion=1,
        carga=codificar_sack([]),
    )))

    canal._esperar_progreso()

    assert enlace.enviados == []
    assert canal._pendientes == {}


# ------------------------------ el cierre no se escala con el backoff


def test_cerrar_no_espera_proporcional_a_un_rto_inflado():
    """Tras darse por vencido, `self._rto` quedo en el techo."""
    enlace = EnlaceFalso()
    canal = CanalSack(enlace)
    canal._rto = RTO_MAXIMO_SACK

    arranque = time.monotonic()
    canal.cerrar()
    tardo = time.monotonic() - arranque

    # 4 * RTO_MAXIMO_SACK serian 32 s esperando a un par que ya se fue.
    assert tardo < 4 * RTO_MAXIMO_SACK
