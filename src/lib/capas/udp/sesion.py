"""Enlace de una sesión del servidor, alimentado por el despachador."""

import logging
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

logger = logging.getLogger(__name__)


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
            logger.debug("[%s] Datagrama encolado (%d bytes)", self._direccion, len(datos))
            return True
        except queue.Full:
            logger.debug("[%s] Cola llena, datagrama descartado", self._direccion)
            return False

    def enviar(self, datos: bytes):
        if self._interrumpido.is_set():
            raise ErrorComunicacion("Sesión interrumpida")
        if len(datos) > TAMANIO_MAX_DATAGRAMA:
            raise ErrorComunicacion("Datagrama demasiado grande")
        try:
            self._conexion.sendto(datos, self._direccion)
            logger.debug("[%s] Enviando datagrama: %d bytes", self._direccion, len(datos))
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
                datos = self._entrada.get(
                    timeout=min(restante, TIMEOUT_DESPACHADOR)
                )
                logger.debug("[%s] Datagrama obtenido de cola (%d bytes)", self._direccion, len(datos))
                return datos
            except queue.Empty:
                continue
        raise ErrorComunicacion("Sesión interrumpida")

    def interrumpir(self):
        logger.debug("[%s] Sesion interrumpida", self._direccion)
        self._interrumpido.set()
