"""Capa de transporte confiable (RDT)."""

from .canal import Canal
from .implementaciones.directo import CanalDirecto
from .errores import ErrorModoNoImplementado, ErrorSegmento
from .fabrica import crear_canal
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
    "ErrorSegmento",
    "ErrorModoNoImplementado",
]
