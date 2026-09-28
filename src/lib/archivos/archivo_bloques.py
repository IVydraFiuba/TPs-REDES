"""Lectura y escritura secuencial de archivos binarios por bloques."""

import os
from pathlib import Path

from lib.archivos.errores_archivos import (
    ErrorArchivoExistente,
    ErrorArchivoInexistente,
    ErrorBloqueArchivo,
    ErrorEscrituraArchivo,
    ErrorEstadoArchivo,
    ErrorLecturaArchivo,
    ErrorTemporalExistente,
)


class LectorArchivo:
    def __init__(self, ruta):
        self.ruta = Path(ruta)
        if not self.ruta.is_file():
            raise ErrorArchivoInexistente(f"No existe el archivo: {self.ruta}")
        try:
            self._archivo = self.ruta.open("rb")
        except OSError as error:
            raise ErrorLecturaArchivo(
                f"No se pudo abrir {self.ruta}: {error}"
            ) from error

    def leer_bloque(self, tamanio):
        """Devuelve hasta tamanio bytes; b'' indica fin del archivo."""
        if not isinstance(tamanio, int) or tamanio <= 0:
            raise ErrorBloqueArchivo("El tamaño del bloque debe ser positivo")
        if self._archivo.closed:
            raise ErrorEstadoArchivo(f"El archivo está cerrado: {self.ruta}")
        try:
            return self._archivo.read(tamanio)
        except OSError as error:
            raise ErrorLecturaArchivo(
                f"No se pudo leer {self.ruta}: {error}"
            ) from error

    def cerrar(self):
        try:
            self._archivo.close()
        except OSError as error:
            raise ErrorLecturaArchivo(
                f"No se pudo cerrar {self.ruta}: {error}"
            ) from error

    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, traza):
        self.cerrar()


class EscritorArchivo:
    """Escribe en .tmp y publica el resultado solo al confirmar."""

    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.ruta_temporal = self.ruta.with_name(self.ruta.name + ".tmp")
        if self.ruta.exists():
            raise ErrorArchivoExistente(f"El archivo ya existe: {self.ruta}")
        if self.ruta_temporal.exists():
            raise ErrorTemporalExistente(
                f"El temporal ya existe: {self.ruta_temporal}"
            )
        try:
            self._archivo = self.ruta_temporal.open("xb")
        except FileExistsError as error:
            raise ErrorTemporalExistente(
                f"El temporal ya existe: {self.ruta_temporal}"
            ) from error
        except OSError as error:
            raise ErrorEscrituraArchivo(
                f"No se pudo crear {self.ruta_temporal}: {error}"
            ) from error
        self._terminado = False

    def escribir_bloque(self, datos):
        if self._terminado:
            raise ErrorEstadoArchivo("La escritura ya terminó")
        if not isinstance(datos, bytes):
            raise ErrorBloqueArchivo("El bloque debe ser de tipo bytes")
        try:
            return self._archivo.write(datos)
        except OSError as error:
            raise ErrorEscrituraArchivo(
                f"No se pudo escribir {self.ruta_temporal}: {error}"
            ) from error

    def confirmar(self):
        """Cierra el temporal y lo mueve al nombre definitivo."""
        if self._terminado:
            raise ErrorEstadoArchivo("La escritura ya terminó")
        try:
            self._archivo.close()
            os.link(self.ruta_temporal, self.ruta)
            self.ruta_temporal.unlink()
        except FileExistsError as error:
            raise ErrorArchivoExistente(
                f"El archivo ya existe: {self.ruta}"
            ) from error
        except OSError as error:
            raise ErrorEscrituraArchivo(
                f"No se pudo confirmar {self.ruta}: {error}"
            ) from error
        self._terminado = True

    def cancelar(self):
        """Descarta una escritura incompleta."""
        if self._terminado:
            return
        try:
            self._archivo.close()
            self.ruta_temporal.unlink(missing_ok=True)
        except OSError as error:
            raise ErrorEscrituraArchivo(
                f"No se pudo cancelar {self.ruta_temporal}: {error}"
            ) from error
        self._terminado = True

    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, traza):
        if not self._terminado:
            self.cancelar()
