"""Selección de RDT para una sesión, independiente de la aplicación."""

from lib.constantes import PROTO_DIRECTO, PROTO_SACK

from .errores import ErrorModoNoImplementado
from .implementaciones.directo import CanalDirecto
from .implementaciones.sack import CanalSack

_CANALES_DISPONIBLES = {
    PROTO_DIRECTO: CanalDirecto,
    PROTO_SACK: CanalSack,
}


def validar_modo(protocolo):
    if protocolo not in _CANALES_DISPONIBLES:
        raise ErrorModoNoImplementado(
            f"Protocolo {protocolo} aún no implementado"
        )


def crear_canal(protocolo, enlace):
    validar_modo(protocolo)
    return _CANALES_DISPONIBLES[protocolo](enlace)
