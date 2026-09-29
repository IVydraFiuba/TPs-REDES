"""Enlace de una sesión del servidor, alimentado por el despachador."""

import queue
import threading
import time

from lib.constantes import (
    TAMANIO_MAX_DATAGRAMA,
    TIMEOUT_DESPACHADOR,
    TIMEOUT_INACTIVIDAD_SESION,
)

from .enlace import Enlace
from .errores import ErrorComunicacion, ErrorTiempoEspera


class EnlaceSesionUdp(Enlace):
    def __init__(self, conexion, direccion, capacidad):
        self._conexion = conexion
        self._direccion = direccion
        self._entrada = queue.Queue(maxsize=capacidad)
        self._interrumpido = threading.Event()

    def entregar(self, datos: bytes) -> bool:
        """Agrega un datagrama a la cola; devuelve False si no hay lugar."""
        if self._interrumpido.is_set():
            return False
        try:
            self._entrada.put_nowait(datos)
            return True
        except queue.Full:
            return False

    def enviar(self, datos: bytes):
        if self._interrumpido.is_set():
            raise ErrorComunicacion("Sesión interrumpida")
        if len(datos) > TAMANIO_MAX_DATAGRAMA:
            raise ErrorComunicacion("Datagrama demasiado grande")
        try:
            self._conexion.sendto(datos, self._direccion)
        except OSError as error:
            raise ErrorComunicacion(f"Error al enviar: {error}") from error

    def recibir(self, timeout=None) -> bytes:
        if timeout is None:
            timeout = TIMEOUT_INACTIVIDAD_SESION
        limite = time.monotonic() + timeout
        while not self._interrumpido.is_set():
            restante = limite - time.monotonic()
            if restante <= 0:
                raise ErrorTiempoEspera("Tiempo de espera agotado")
            try:
                return self._entrada.get(
                    timeout=min(restante, TIMEOUT_DESPACHADOR)
                )
            except queue.Empty:
                continue
        raise ErrorComunicacion("Sesión interrumpida")

    def interrumpir(self):
        self._interrumpido.set()
