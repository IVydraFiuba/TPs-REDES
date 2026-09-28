"""Recepción de sesiones UDP, todavía secuencial."""

import logging
import socket
import threading

from lib.archivos.almacenamiento_servidor import AlmacenamientoServidor
from lib.constantes import PROTO_DIRECTO, TAMANIO_MAX_DATAGRAMA, TIMEOUT_SERVIDOR
from lib.rdt.errores import ErrorSegmento
from lib.rdt.fabrica import crear_canal
from lib.rdt.segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)
from lib.udp import EnlaceUdp
from lib.udp.errores import ErrorComunicacion

from .sesion import SesionServidor

logger = logging.getLogger(__name__)


class Servidor:
    def __init__(self, host, port, almacenamiento):
        self._host = host
        self._port = port
        self._almacenamiento = AlmacenamientoServidor(almacenamiento)
        self._detener = threading.Event()

    def iniciar_servidor(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            conexion.bind((self._host, self._port))
            conexion.settimeout(TIMEOUT_SERVIDOR)
            logger.info("Servidor escuchando en %s:%s", self._host, self._port)
            while not self._detener.is_set():
                try:
                    datos, direccion = conexion.recvfrom(TAMANIO_MAX_DATAGRAMA + 1)
                except socket.timeout:
                    continue
                try:
                    segmento = decodificar_segmento(datos)
                    if segmento.tipo != TipoSegmento.SYN or len(segmento.carga) != 1:
                        continue
                    protocolo = segmento.carga[0]
                    if protocolo != PROTO_DIRECTO:
                        logger.warning("Modo %s no implementado", protocolo)
                        continue
                    enlace = EnlaceUdp(conexion, direccion)
                    canal = crear_canal(protocolo, enlace, segmento.sesion)
                    enlace.enviar(codificar_segmento(Segmento(
                        TipoSegmento.SYN, segmento.sesion, carga=segmento.carga)))
                    SesionServidor(canal, self._almacenamiento).ejecutar()
                except (ErrorSegmento, ErrorComunicacion) as error:
                    logger.warning("Datagrama de %s descartado: %s", direccion, error)
            logger.info("Servidor detenido")

    def apagar_servidor(self):
        self._detener.set()
