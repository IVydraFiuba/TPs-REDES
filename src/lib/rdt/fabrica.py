"""Selección de RDT para una sesión, independiente de la aplicación."""

from lib.constantes import PROTO_DIRECTO

from .errores import ErrorModoNoImplementado
from .implementaciones.directo import CanalDirecto


def crear_canal(protocolo, enlace, sesion):
    if protocolo == PROTO_DIRECTO:
        return CanalDirecto(enlace, sesion)
    raise ErrorModoNoImplementado(f"Protocolo {protocolo} aún no implementado")
