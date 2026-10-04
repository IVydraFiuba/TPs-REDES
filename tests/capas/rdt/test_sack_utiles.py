from lib.capas.rdt.sack_utiles import (
    codificar_sack,
    codificar_ack_sack,
    decodificar_sack,
)
from lib.capas.rdt.segmento import decodificar_segmento


def test_codificar_y_decodificar_sack():
    """Verifica que los rangos SACK se conserven al codificar y decodificar."""
    rangos_originales = [(3, 5), (8, 9), (11, 13)]

    datos = codificar_sack(rangos_originales)
    rangos_recuperados = decodificar_sack(datos)

    assert rangos_recuperados == rangos_originales


def test_codificar_ack_sack():
    """Verifica que ACK y rangos SACK se codifiquen correctamente."""
    confirmacion = 2
    rangos = [(3, 5), (8, 9)]

    datos = codificar_ack_sack(confirmacion, rangos)

    segmento = decodificar_segmento(datos)
    rangos_recuperados = decodificar_sack(segmento.carga)

    assert segmento.confirmacion == confirmacion
    assert rangos_recuperados == rangos