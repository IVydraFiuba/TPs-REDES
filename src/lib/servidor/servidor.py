"""Ciclo de vida del socket UDP compartido por las sesiones."""

import logging
import socket
import threading

from lib.archivos.almacenamiento_servidor import AlmacenamientoServidor
from lib.constantes import TAMANIO_BUFFER_RECEPCION_UDP

from .despachador import Despachador

logger = logging.getLogger(__name__)


class Servidor:
    def __init__(self, host, port, almacenamiento):
        self._host = host
        self._port = port
        self._almacenamiento = AlmacenamientoServidor(almacenamiento)
        self._detener = threading.Event()

    def iniciar_servidor(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            conexion.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF,
                TAMANIO_BUFFER_RECEPCION_UDP,
            )
            conexion.bind((self._host, self._port))
            logger.info("Servidor escuchando en %s:%s", self._host, self._port)
            despachador = Despachador(
                conexion,
                self._almacenamiento,
                self._detener,
            )
            despachador.ejecutar()
            logger.info("Servidor detenido")

    def apagar_servidor(self):
        self._detener.set()
