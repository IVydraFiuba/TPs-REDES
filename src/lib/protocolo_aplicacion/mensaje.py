"""Representación de los mensajes de aplicación."""

from dataclasses import dataclass
from enum import IntEnum


class TipoMensaje(IntEnum):
    SOLICITUD_SUBIDA = 1
    SOLICITUD_DESCARGA = 2
    ACEPTADO = 3
    BLOQUE_ARCHIVO = 4
    FIN_ARCHIVO = 5
    COMPLETADO = 6
    ERROR = 7


@dataclass(frozen=True)
class Mensaje:
    tipo: TipoMensaje
    carga: bytes = b""
