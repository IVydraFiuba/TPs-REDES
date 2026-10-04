"""Selección de RDT para una sesión, independiente de la aplicación."""

from lib.constantes import PROTO_DIRECTO
from lib.constantes import PROTO_SW
from lib.constantes import PROTO_SACK

from .errores import ErrorModoNoImplementado
from .implementaciones.directo import CanalDirecto
from .implementaciones.stopwait import CanalStopWait

_CANALES_DISPONIBLES = {
    PROTO_DIRECTO: CanalDirecto,
    PROTO_SW: CanalStopWait,
    PROTO_SACK: CanalStopWait
}


def validar_modo(protocolo):
    if protocolo not in _CANALES_DISPONIBLES:
        raise ErrorModoNoImplementado(
            f"Protocolo {protocolo} aún no implementado"
        )


def crear_canal(protocolo, enlace):
    validar_modo(protocolo)
    return _CANALES_DISPONIBLES[protocolo](enlace)
