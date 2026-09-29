"""Canal sin recuperación de pérdidas, con encapsulación de segmentos."""

from lib.rdt.canal import Canal
from lib.rdt.errores import ErrorSegmento
from lib.rdt.segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)


class CanalDirecto(Canal):
    def __init__(self, enlace):
        self._enlace = enlace

    def enviar(self, datos: bytes):
        self._enlace.enviar(codificar_segmento(
            Segmento(TipoSegmento.DATOS, carga=datos)))

    def recibir(self) -> bytes:
        segmento = decodificar_segmento(self._enlace.recibir())
        if segmento.tipo != TipoSegmento.DATOS:
            raise ErrorSegmento("Segmento inesperado")
        return segmento.carga

    def vaciar(self):
        pass

    def cerrar(self):
        pass
