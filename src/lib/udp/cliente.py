"""Enlace UDP del cliente, propietario de su socket."""

import socket
import time

from lib.constantes import (
    TAMANIO_BUFFER_RECEPCION_UDP,
    TAMANIO_MAX_DATAGRAMA,
    TIMEOUT_CLIENTE,
)

from .enlace import Enlace
from .errores import ErrorComunicacion, ErrorTiempoEspera


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
        except OSError as error:
            raise ErrorComunicacion(f"Error al enviar: {error}") from error

    def recibir(self) -> bytes:
        limite = time.monotonic() + TIMEOUT_CLIENTE
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise ErrorTiempoEspera("Tiempo de espera agotado")
            try:
                self._conexion.settimeout(min(restante, 0.2))
                datos, direccion = self._conexion.recvfrom(
                    TAMANIO_MAX_DATAGRAMA + 1
                )
            except socket.timeout:
                continue
            except OSError as error:
                raise ErrorComunicacion(
                    f"Error al recibir: {error}"
                ) from error
            if direccion != self._direccion:
                continue
            if len(datos) > TAMANIO_MAX_DATAGRAMA:
                raise ErrorComunicacion("Datagrama demasiado grande")
            return datos
