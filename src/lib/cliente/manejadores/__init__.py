"""Manejadores de operaciones de cliente."""

from .descarga import manejador_descarga
from .subida import manejador_subida

__all__ = ["manejador_subida", "manejador_descarga"]
