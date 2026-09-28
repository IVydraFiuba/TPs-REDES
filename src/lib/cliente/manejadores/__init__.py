"""Manejadores de operaciones de cliente."""

from .download import manejador_descarga
from .upload import manejador_subida

__all__ = ["manejador_subida", "manejador_descarga"]
