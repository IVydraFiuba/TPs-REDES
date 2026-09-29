"""Punto de extensión para el futuro canal Stop-and-Wait."""

from ..canal import Canal
from ..errores import ErrorModoNoImplementado


class CanalStopWait(Canal):
    def __init__(self, enlace):
        raise ErrorModoNoImplementado(
            "Stop-and-Wait aún no implementado"
        )

    def enviar(self, datos: bytes):
        raise ErrorModoNoImplementado

    def recibir(self) -> bytes:
        raise ErrorModoNoImplementado

    def vaciar(self):
        raise ErrorModoNoImplementado

    def cerrar(self):
        raise ErrorModoNoImplementado
