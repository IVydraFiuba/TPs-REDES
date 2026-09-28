"""Paquete protocolo de aplicación."""

from .errores import (
    ErrorComunicacion,
    ErrorMensaje,
    ErrorModoNoImplementado,
    ErrorOperacionRemota,
    ErrorProtocolo,
    ErrorRespuesta,
    ErrorServidorOcupado,
    ErrorTiempoEspera,
    ErrorTransferenciaIncompleta,
)
from .mensajes import (
    codificar_error,
    codificar_mensaje,
    codificar_solicitud,
    decodificar_error,
    decodificar_mensaje,
    decodificar_solicitud,
)

__all__ = [
    "ErrorProtocolo",
    "ErrorMensaje",
    "ErrorComunicacion",
    "ErrorTiempoEspera",
    "ErrorServidorOcupado",
    "ErrorModoNoImplementado",
    "ErrorOperacionRemota",
    "ErrorRespuesta",
    "ErrorTransferenciaIncompleta",
    "codificar_mensaje",
    "decodificar_mensaje",
    "codificar_solicitud",
    "decodificar_solicitud",
    "codificar_error",
    "decodificar_error",
]
