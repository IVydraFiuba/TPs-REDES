"""Definición del formato de segmento para la capa de transporte.

Cada segmento tiene una cabecera de 7 bytes seguida de payload opcional.

Cabecera: tipo(1) | seq(4) | largo(2) (puede cambiar)
"""

import struct
from collections import namedtuple

from lib.constantes import TAMANIO_BLOQUE

DATA = 0
ACK = 1
SYN = 2
FIN = 3

_CABECERA = struct.Struct("!BIH")
TAM_CABECERA = _CABECERA.size

Segmento = namedtuple("Segmento", ["tipo", "seq", "payload"])

MAX_PAYLOAD = TAMANIO_BLOQUE


def empaquetar(tipo, seq, payload=b""):
    """Empaqueta un segmento.

    Args:
        tipo: DATA, ACK, SYN o FIN
        seq: número de secuencia
        payload: datos del segmento

    Returns:
        bytes: segmento codificado
    """
    longitud = len(payload)
    if payload and longitud > MAX_PAYLOAD:
        raise ValueError(
            f"Payload demasiado grande: {longitud} > {MAX_PAYLOAD}"
        )
    cabecera = _CABECERA.pack(tipo, seq, longitud)
    return cabecera + payload


def desempaquetar(datos):
    """Desempaqueta un segmento.

    Args:
        datos: bytes del segmento

    Returns:
        Segmento(nombre, seq, payload)
    """
    if len(datos) < TAM_CABECERA:
        raise ValueError(
            f"Datagrama demasiado corto: {len(datos)} < {TAM_CABECERA}"
        )
    tipo, seq, longitud = _CABECERA.unpack(datos[:TAM_CABECERA])
    payload = datos[TAM_CABECERA:TAM_CABECERA + longitud]
    if len(payload) != longitud:
        raise ValueError(
            f"Longitud不一致: cabecera={longitud}, real={len(payload)}"
        )
    return Segmento(tipo, seq, payload)


def tipo_nombre(tipo):
    """Retorna el nombre del tipo de segmento."""
    return {DATA: "DATA", ACK: "ACK", SYN: "SYN", FIN: "FIN"}.get(tipo, "?")
