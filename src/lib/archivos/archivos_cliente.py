"""Validaciones locales del cliente para subir y descargar archivos."""

from pathlib import Path

from lib.archivos.archivo_bloques import EscritorArchivo, LectorArchivo
from lib.archivos.errores_archivos import (
    ErrorDirectorioDestino,
    ErrorNombreArchivo,
)


def abrir_origen_subida(ruta_origen):
    """Valida el origen y devuelve un lector para usar con `with`."""
    ruta = Path(ruta_origen)
    if ruta.suffix == ".tmp":
        raise ErrorNombreArchivo(f"No se puede subir un temporal: {ruta}")
    return LectorArchivo(ruta)


def preparar_destino_descarga(ruta_destino):
    """Devuelve un escritor temporal; espera la ruta completa del archivo."""
    ruta = Path(ruta_destino)
    if not ruta.parent.is_dir() or ruta.is_dir():
        raise ErrorDirectorioDestino(
            f"El destino debe ser un archivo dentro de un directorio: {ruta}"
        )
    return EscritorArchivo(ruta)
