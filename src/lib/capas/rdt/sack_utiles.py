import struct

from .segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
)

_RANGO = struct.Struct("!II")


def codificar_sack(rangos):
    """Codifica una lista de rangos de números de secuencia.
    Cada rango se representa mediante dos enteros de 4 bytes:
    el número de secuencia inicial y el número de secuencia final."""

    datos = b""

    for inicio, fin in rangos:
        datos += _RANGO.pack(inicio, fin)

    return datos


def decodificar_sack(datos):
    """Decodifica una lista de rangos de números de secuencia.
    Cada rango ocupa 8 bytes: 4 bytes para el número de secuencia inicial
    y 4 bytes para el número de secuencia final."""

    rangos = []

    for posicion in range(0, len(datos), _RANGO.size):
        inicio, fin = _RANGO.unpack_from(datos, posicion)
        rangos.append((inicio, fin))

    return rangos

def codificar_ack_sack(confirmacion, rangos):
    """Construye un segmento ACK para SACK. 
    confirmacion indica el próximo número de secuencia que se espera recibir en orden.
    rangos contiene la lista de rangos de números de secuencia ya recibidos mayores que confirmación."""

    carga = codificar_sack(rangos)

    segmento = Segmento(
        tipo=TipoSegmento.ACK,
        confirmacion=confirmacion,
        carga=carga,
    )

    return codificar_segmento(segmento)