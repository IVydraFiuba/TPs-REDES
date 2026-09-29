"""Enlace UDP del cliente, propietario de su socket."""

import logging
import socket
import time

from lib.constantes import (
    TAMANIO_BUFFER_RECEPCION_UDP,
    TAMANIO_MAX_DATAGRAMA,
    TIMEOUT_INACTIVIDAD_SESION,
)

from .enlace import Enlace
from .errores import ErrorComunicacion, ErrorTiempoEspera

logger = logging.getLogger(__name__)


class EnlaceClienteUdp(Enlace):
    def __init__(self, conexion, direccion):
        self._conexion = conexion
        try:
            self._conexion.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF,
                TAMANIO_BUFFER_RECEPCION_UDP,
            )
            self._direccion = (
                socket.gethostbyname(direccion[0]),
                direccion[1],
            )
        except OSError as error:
            raise ErrorComunicacion(
                f"No se pudo preparar el enlace: {error}"
            ) from error

    def enviar(self, datos: bytes):
        if len(datos) > TAMANIO_MAX_DATAGRAMA:
            raise ErrorComunicacion("Datagrama demasiado grande")
        try:
            self._conexion.sendto(datos, self._direccion)
            logger.debug("Enviando a %s: %d bytes", self._direccion, len(datos))
        except OSError as error:
            raise ErrorComunicacion(f"Error al enviar: {error}") from error

    def recibir(self, timeout=None) -> bytes:
        if timeout is None:
            timeout = TIMEOUT_INACTIVIDAD_SESION
        limite = time.monotonic() + timeout
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise ErrorTiempoEspera("Tiempo de espera agotado")
            try:
                self._conexion.settimeout(restante)
                datos, direccion = self._conexion.recvfrom(
                    TAMANIO_MAX_DATAGRAMA + 1
                )
            except socket.timeout as error:
                logger.debug("Timeout esperando respuesta de %s", self._direccion)
                raise ErrorTiempoEspera(
                    "Tiempo de espera agotado"
                ) from error
            except OSError as error:
                raise ErrorComunicacion(
                    f"Error al recibir: {error}"
                ) from error
            if direccion != self._direccion:
                continue
            if len(datos) > TAMANIO_MAX_DATAGRAMA:
                raise ErrorComunicacion("Datagrama demasiado grande")
            logger.debug("Recibido de %s: %d bytes", direccion, len(datos))
            return datos
