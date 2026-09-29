"""Operaciones de archivo sobre mensajes de aplicación y un canal RDT."""

import logging
import socket

from lib.cliente.manejadores import manejador_descarga, manejador_subida
from lib.constantes import PROTO_DIRECTO, PROTOCOLS
from lib.protocolo_aplicacion import ComunicadorAplicacion
from lib.rdt.errores import ErrorModoNoImplementado
from lib.rdt.establecimiento import solicitar_sesion
from lib.rdt.fabrica import crear_canal
from lib.udp import EnlaceClienteUdp

logger = logging.getLogger(__name__)


def parsear_protocolo(nombre):
    try:
        return PROTOCOLS[nombre]
    except KeyError as error:
        raise ErrorModoNoImplementado(
            f"Protocolo desconocido: {nombre}"
        ) from error


class Cliente:
    def __init__(self, host, port, protocolo):
        self._direccion = (host, port)
        self._protocolo = parsear_protocolo(protocolo)

    def _abrir_canal(self, conexion):
        # Eliminar esta validación al implementar Stop-and-Wait y SACK.
        if self._protocolo != PROTO_DIRECTO:
            raise ErrorModoNoImplementado(
                f"Protocolo {self._protocolo} aún no implementado")

        enlace = EnlaceClienteUdp(conexion, self._direccion)
        solicitar_sesion(enlace, self._protocolo)
        return crear_canal(self._protocolo, enlace)

    def subir(self, origen, nombre):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            canal = self._abrir_canal(conexion)
            try:
                manejador_subida(
                    ComunicadorAplicacion(canal), origen, nombre
                )
            finally:
                canal.cerrar()

    def descargar(self, destino, nombre):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            canal = self._abrir_canal(conexion)
            try:
                manejador_descarga(
                    ComunicadorAplicacion(canal), destino, nombre
                )
            finally:
                canal.cerrar()
