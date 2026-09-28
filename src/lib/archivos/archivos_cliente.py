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
    """Valida el destino y devuelve un escritor para usar con `with`.

    Si ruta_destino es un directorio, se debe llamar con el nombre
    del archivo ya concatenado. Esta función solo acepta rutas a archivos.
    """
    ruta = Path(ruta_destino)
    if not ruta.parent.is_dir() or ruta.is_dir():
        raise ErrorDirectorioDestino(
            f"El destino debe ser un archivo dentro de un directorio: {ruta}"
        )
    return EscritorArchivo(ruta)
