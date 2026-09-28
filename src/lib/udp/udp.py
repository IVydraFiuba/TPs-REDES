"""Enlace por par UDP; solo el despachador leerá del socket al agregar concurrencia."""

import socket
import time

from lib.constantes import TAMANIO_MAX_DATAGRAMA, TIMEOUT_CLIENTE

from .errores import ErrorComunicacion, ErrorTiempoEspera


class EnlaceUdp:
    def __init__(self, conexion, direccion, datagrama_inicial=None):
        self._conexion = conexion
        self._direccion = direccion
        self._inicial = datagrama_inicial

    def enviar(self, datos):
        if len(datos) > TAMANIO_MAX_DATAGRAMA:
            raise ErrorComunicacion("Datagrama demasiado grande")
        try:
            self._conexion.sendto(datos, self._direccion)
        except OSError as error:
            raise ErrorComunicacion(f"Error al enviar: {error}") from error

    def recibir(self):
        if self._inicial is not None:
            datos, self._inicial = self._inicial, None
            return datos
        limite = time.monotonic() + TIMEOUT_CLIENTE
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise ErrorTiempoEspera("Tiempo de espera agotado")
            try:
                self._conexion.settimeout(min(restante, 0.2))
                datos, direccion = self._conexion.recvfrom(TAMANIO_MAX_DATAGRAMA + 1)
            except socket.timeout:
                continue
            except OSError as error:
                raise ErrorComunicacion(f"Error al recibir: {error}") from error
            if direccion != self._direccion:
                continue
            if len(datos) > TAMANIO_MAX_DATAGRAMA:
                raise ErrorComunicacion("Datagrama demasiado grande")
            return datos
