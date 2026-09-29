"""Punto de extensión para el futuro canal con SACK."""

from ..canal import Canal
from ..errores import ErrorModoNoImplementado


class CanalSack(Canal):
    def __init__(self, enlace):
        raise ErrorModoNoImplementado("SACK aún no implementado")

    def enviar(self, datos: bytes):
        raise ErrorModoNoImplementado

    def recibir(self) -> bytes:
        raise ErrorModoNoImplementado

    def vaciar(self):
        raise ErrorModoNoImplementado

    def cerrar(self):
        raise ErrorModoNoImplementado
