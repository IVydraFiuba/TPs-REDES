# lib/segmento.py
"""Formato de segmento, comun a Stop & Wait y SACK.

Cabecera de 7 bytes en formato de red (!BIH):

    tipo(1) | seq(4) | largo(2)

    DATA   : seq   = numero de segmento (base 0)
             largo = bytes de payload, seguidos del payload
    ACK    : seq   = proximo segmento esperado (ACK acumulativo)
             largo = cantidad de bloques SACK, seguidos de los bloques
    FIN    : seq   = total de segmentos enviados

Cada bloque SACK son dos enteros de 32 bits (!II): el primero y el
ultimo numero de segmento de un tramo recibido, los dos incluidos.
El bloque (3, 7) significa "tengo el 3, 4, 5, 6, 7"; (7, 7) es un tramo
de un solo segmento.
Los bloques arrancan siempre por encima del proximo esperado: lo que
ya cubre el ACK acumulativo no se repite. Sirven para retransmitir
solo lo que falta: si el proximo esperado es el 5 y viene el bloque
(7, 8), el emisor deduce que el 5 y el 6 no llegaron y retransmite
solo esos.

Stop & Wait usa esta misma cabecera con largo = 0 en sus ACKs, es
decir, sin bloques.
"""
import struct
from collections import namedtuple

from borrador.constants import PAYLOAD_SIZE

DATA = 0
ACK = 1
FIN = 2

_CABECERA = "!BIH"
_BLOQUE = "!II"

TAM_CABECERA = struct.calcsize(_CABECERA)
TAM_BLOQUE = struct.calcsize(_BLOQUE)
MAX_BLOQUES_SACK = 8
TAM_MAX_SEGMENTO = TAM_CABECERA + PAYLOAD_SIZE

Segmento = namedtuple("Segmento", ["tipo", "seq", "payload", "bloques"])


def empaquetar_data(seq, payload):
    if len(payload) > PAYLOAD_SIZE:
        raise ValueError(f"payload de {len(payload)} bytes, "
                         f"el maximo es {PAYLOAD_SIZE}")
    return struct.pack(_CABECERA, DATA, seq, len(payload)) + payload


def empaquetar_ack(proximo, bloques=()):
    if len(bloques) > MAX_BLOQUES_SACK:
        raise ValueError(f"el maximo es {MAX_BLOQUES_SACK} bloques SACK")
    datos = struct.pack(_CABECERA, ACK, proximo, len(bloques))
    for primero, ultimo in bloques:
        if primero > ultimo:
            raise ValueError(f"bloque invertido: ({primero}, {ultimo})")
        datos += struct.pack(_BLOQUE, primero, ultimo)
    return datos


def empaquetar_fin(total_segmentos=0):
    return struct.pack(_CABECERA, FIN, total_segmentos, 0)


def desempaquetar(datos):
    """Devuelve un Segmento. Lanza ValueError si esta mal formado."""
    if len(datos) < TAM_CABECERA:
        raise ValueError("segmento mas corto que la cabecera")

    tipo, seq, largo = struct.unpack(_CABECERA, datos[:TAM_CABECERA])
    cuerpo = datos[TAM_CABECERA:]

    if tipo == DATA:
        if len(cuerpo) != largo:
            raise ValueError(f"payload truncado: dice {largo} bytes, "
                             f"llegaron {len(cuerpo)}")
        return Segmento(tipo, seq, cuerpo, ())

    if tipo == ACK:
        if len(cuerpo) != largo * TAM_BLOQUE:
            raise ValueError(f"dice {largo} bloques, "
                             f"llegaron {len(cuerpo)} bytes")
        bloques = tuple(
            struct.unpack(_BLOQUE, cuerpo[i:i + TAM_BLOQUE])
            for i in range(0, len(cuerpo), TAM_BLOQUE)
        )
        return Segmento(tipo, seq, b"", bloques)

    if tipo == FIN:
        if largo != 0 or cuerpo:
            raise ValueError(f"el tipo {tipo} no lleva cuerpo")
        return Segmento(tipo, seq, b"", ())

    raise ValueError(f"tipo de segmento desconocido: {tipo}")
