import time

import pytest

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
from lib.constantes import RTO_MAXIMO_SACK, VENTANA_SACK


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

    canal._rto = 0.01

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
