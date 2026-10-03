"""Punto de extensión para el futuro canal con SACK."""

import logging
import threading

from ..canal import Canal
from ..errores import ErrorModoNoImplementado
from ..segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
)

logger = logging.getLogger(__name__)

class CanalSack(Canal):
    def __init__(self, enlace):
        self._enlace = enlace
        self._proxima_secuencia = 0

    def enviar(self, datos: bytes):
        segmento = Segmento(
            tipo=TipoSegmento.DATOS,
            secuencia=self._proxima_secuencia,
            carga=datos,
        )

        logger.debug(
        "[%s] Enviando segmento DATOS seq=%d: %d bytes",
        threading.current_thread().name,
        self._proxima_secuencia,
        len(datos),
    )

        self._enlace.enviar(codificar_segmento(segmento))
        self._proxima_secuencia += 1

    def recibir(self) -> bytes:
        raise ErrorModoNoImplementado

    def vaciar(self):
        raise ErrorModoNoImplementado

    def cerrar(self):
        raise ErrorModoNoImplementado
