"""Operaciones de archivo sobre mensajes de aplicación y un canal RDT."""

import logging
import socket

from lib.cliente.manejadores import manejador_descarga, manejador_subida
from lib.capas.pca import ComunicadorAplicacion
from lib.capas.rdt.errores import ErrorModoNoImplementado
from lib.capas.rdt.establecimiento import solicitar_sesion
from lib.capas.rdt.fabrica import crear_canal, validar_modo
from lib.capas.udp import EnlaceClienteUdp
from lib.constantes import PROTOCOLS

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
        validar_modo(self._protocolo)
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
