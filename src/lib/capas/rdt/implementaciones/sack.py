"""Punto de extensión para el futuro canal con SACK."""

from ..canal import Canal
from ..errores import ErrorModoNoImplementado
from lib.constantes import TAMANIO_MAX_CARGA_SEGMENTO
from ..segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
)

class CanalSack(Canal):
    def __init__(self, enlace):
        self._enlace = enlace
        self._proxima_secuencia = 0

    def enviar(self, datos: bytes):
        for inicio in range(0, len(datos), TAMANIO_MAX_CARGA_SEGMENTO):
            bloque = datos[inicio:inicio + TAMANIO_MAX_CARGA_SEGMENTO]

            segmento = Segmento(
                tipo=TipoSegmento.DATOS,
                secuencia=self._proxima_secuencia,
                carga=bloque,
            )

            self._enlace.enviar(codificar_segmento(segmento))
            self._proxima_secuencia += 1

    def recibir(self) -> bytes:
        raise ErrorModoNoImplementado

    def vaciar(self):
        raise ErrorModoNoImplementado

    def cerrar(self):
        raise ErrorModoNoImplementado
