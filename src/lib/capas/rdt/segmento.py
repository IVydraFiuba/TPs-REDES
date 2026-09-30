"""Formato compartido por directo, Stop-and-Wait y SACK.

tipo(1), secuencia(4), ack(4), longitud(2), carga.
"""

import struct
from dataclasses import dataclass
from enum import IntEnum

from lib.constantes import TAMANIO_MAX_CARGA_SEGMENTO, TAMANIO_MAX_DATAGRAMA

from .errores import ErrorSegmento


class TipoSegmento(IntEnum):
    SYN = 1
    ACK = 2
    DATOS = 3
    FIN = 4


_CABECERA = struct.Struct("!BIIH")
assert _CABECERA.size == TAMANIO_MAX_DATAGRAMA - TAMANIO_MAX_CARGA_SEGMENTO


@dataclass(frozen=True)
class Segmento:
    tipo: TipoSegmento
    secuencia: int = 0
    confirmacion: int = 0
    carga: bytes = b""


def codificar_segmento(segmento):
    if (not isinstance(segmento, Segmento)
            or not isinstance(segmento.tipo, TipoSegmento)):
        raise ErrorSegmento("Segmento inválido")
    if (not isinstance(segmento.carga, bytes)
            or len(segmento.carga) > TAMANIO_MAX_CARGA_SEGMENTO):
        raise ErrorSegmento("Carga de segmento inválida")
    if any(type(n) is not int or not 0 <= n <= 0xffffffff for n in
           (segmento.secuencia, segmento.confirmacion)):
        raise ErrorSegmento("Secuencia o confirmación inválidas")
    return _CABECERA.pack(segmento.tipo,
                          segmento.secuencia, segmento.confirmacion,
                          len(segmento.carga)) + segmento.carga


def decodificar_segmento(datos):
    if len(datos) < _CABECERA.size or len(datos) > TAMANIO_MAX_DATAGRAMA:
        raise ErrorSegmento("Tamaño de segmento inválido")
    tipo, secuencia, confirmacion, longitud = (
        _CABECERA.unpack_from(datos)
    )
    if longitud != len(datos) - _CABECERA.size:
        raise ErrorSegmento("Longitud de segmento inválida")
    try:
        return Segmento(TipoSegmento(tipo), secuencia, confirmacion,
                        datos[_CABECERA.size:])
    except ValueError as error:
        raise ErrorSegmento(f"Tipo de segmento desconocido: {tipo}") from error
