"""Capa de transferencia confiable (RDT)."""

from .canal import Canal
from .implementaciones.directo import CanalDirecto
from .errores import ErrorModoNoImplementado, ErrorSegmento
from .establecimiento import (
    codificar_syn,
    leer_solicitud_sesion,
    solicitar_sesion,
)
from .fabrica import crear_canal, validar_modo
from .segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)

__all__ = [
    "Canal",
    "CanalDirecto",
    "Segmento",
    "TipoSegmento",
    "codificar_segmento",
    "decodificar_segmento",
    "crear_canal",
    "validar_modo",
    "codificar_syn",
    "leer_solicitud_sesion",
    "solicitar_sesion",
    "ErrorSegmento",
    "ErrorModoNoImplementado",
]
