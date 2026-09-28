"""Reglas del servidor para nombres y subidas, sin lógica de red."""

import threading
from contextlib import contextmanager
from pathlib import Path

from lib.archivos.archivo_bloques import EscritorArchivo, LectorArchivo
from lib.archivos.errores_archivos import (
    ErrorAlmacenamiento,
    ErrorArchivoExistente,
    ErrorNombreArchivo,
    ErrorTransferenciaEnCurso,
)


class AlmacenamientoServidor:
    def __init__(self, directorio):
        self._directorio = Path(directorio)
        try:
            self._directorio.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise ErrorAlmacenamiento(
                f"No se pudo preparar {self._directorio}: {error}"
            ) from error
        if not self._directorio.is_dir():
            raise ErrorAlmacenamiento(
                f"No es un directorio: {self._directorio}"
            )
        self._cerrojo = threading.Lock()
        self._subidas_activas = set()

    def _ruta(self, nombre):
        if (
            not isinstance(nombre, str)
            or not nombre
            or nombre in (".", "..")
            or "/" in nombre
            or "\\" in nombre
            or "\x00" in nombre
            or nombre.endswith(".tmp")
        ):
            raise ErrorNombreArchivo(
                f"Nombre de archivo inválido: {nombre!r}"
            )
        ruta = self._directorio / nombre
        if ruta.is_symlink():
            raise ErrorNombreArchivo(f"No se aceptan enlaces: {nombre}")
        return ruta

    def abrir_descarga(self, nombre):
        """El llamador cierra el lector con `with`."""
        return LectorArchivo(self._ruta(nombre))

    @contextmanager
    def recibir_subida(self, nombre):
        """Reserva el nombre hasta salir del `with`, incluso ante errores.

        El llamador debe ejecutar `escritor.confirmar()` al recibir el fin
        completo. Si sale sin confirmar, se descarta el temporal.
        """
        ruta = self._ruta(nombre)
        with self._cerrojo:
            if nombre in self._subidas_activas:
                raise ErrorTransferenciaEnCurso(
                    f"Ya se está subiendo el archivo: {nombre}"
                )
            if ruta.exists():
                raise ErrorArchivoExistente(
                    f"El archivo ya existe: {nombre}"
                )
            self._subidas_activas.add(nombre)
        try:
            with EscritorArchivo(ruta) as escritor:
                yield escritor
        finally:
            with self._cerrojo:
                self._subidas_activas.remove(nombre)
