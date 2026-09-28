"""Operaciones de archivo sobre mensajes de aplicación y un canal RDT."""

import logging
import secrets
import socket

from lib.cliente.manejadores import manejador_descarga, manejador_subida
from lib.constantes import PROTO_DIRECTO, PROTOCOLS
from lib.rdt.errores import ErrorModoNoImplementado, ErrorSegmento
from lib.rdt.fabrica import crear_canal
from lib.rdt.segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)
from lib.udp import EnlaceUdp

logger = logging.getLogger(__name__)


def parsear_protocolo(nombre):
    try:
        return PROTOCOLS[nombre]
    except KeyError as error:
        raise ErrorModoNoImplementado(f"Protocolo desconocido: {nombre}") from error


class Cliente:
    def __init__(self, host, port, protocolo):
        self._direccion = (host, port)
        self._protocolo = parsear_protocolo(protocolo)

    def _abrir_canal(self, conexion):
        if self._protocolo != PROTO_DIRECTO: # ELIMINAR ESTE IF CUANDO IMPLEMENTEMOS SW Y SACK
            raise ErrorModoNoImplementado(
                f"Protocolo {self._protocolo} aún no implementado")
        
        enlace = EnlaceUdp(conexion, self._direccion)
        sesion = secrets.randbits(32)
        enlace.enviar(
            codificar_segmento(
                Segmento(
                    TipoSegmento.SYN, 
                    sesion, 
                    carga=bytes([self._protocolo])
                    )
                )
            )
        respuesta = decodificar_segmento(enlace.recibir())

        if (respuesta.tipo != TipoSegmento.SYN or respuesta.sesion != sesion
                or respuesta.carga != bytes([self._protocolo])):
            raise ErrorSegmento("Respuesta de establecimiento inesperada")
        return crear_canal(self._protocolo, enlace, sesion)

    def subir(self, origen, nombre):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            canal = self._abrir_canal(conexion)
            try:
                manejador_subida(canal, origen, nombre)
            finally:
                canal.cerrar()

    def descargar(self, destino, nombre):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            canal = self._abrir_canal(conexion)
            try:
                manejador_descarga(canal, destino, nombre)
            finally:
                canal.cerrar()
