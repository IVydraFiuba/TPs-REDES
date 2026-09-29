"""Canal sin recuperación de pérdidas, con encapsulación de segmentos."""

import logging
import threading

from ..canal import Canal
from ..errores import ErrorSegmento
from ..segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)

logger = logging.getLogger(__name__)


class CanalDirecto(Canal):
    def __init__(self, enlace):
        self._enlace = enlace

    def enviar(self, datos: bytes):
        logger.debug(
            "[%s] Enviando segmento DATOS: %d bytes",
            threading.current_thread().name,
            len(datos)
        )
        self._enlace.enviar(codificar_segmento(
            Segmento(TipoSegmento.DATOS, carga=datos)))

    def recibir(self) -> bytes:
        segmento = decodificar_segmento(self._enlace.recibir())
        if segmento.tipo != TipoSegmento.DATOS:
            raise ErrorSegmento("Segmento inesperado")
        logger.debug(
            "[%s] Recibido segmento DATOS: %d bytes",
            threading.current_thread().name,
            len(segmento.carga)
        )
        return segmento.carga

    def vaciar(self):
        pass

    def cerrar(self):
        pass
