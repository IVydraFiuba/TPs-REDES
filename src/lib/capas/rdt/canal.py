"""Interfaz que consume la aplicación; no expone direcciones ni ACK."""

from abc import ABC, abstractmethod


class Canal(ABC):
    @abstractmethod
    def enviar(self, datos: bytes):
        """Admite un mensaje completo de la capa de aplicación.

        Un canal con ventana puede conservarlo como envío pendiente. La
        aplicación no conoce segmentos, secuencias ni confirmaciones.
        """

    @abstractmethod
    def recibir(self) -> bytes:
        """Devuelve el siguiente mensaje completo del par.

        Los modos confiables deben entregarlo en orden y una sola vez, aunque
        durante la espera procesen ACK u otros segmentos de control.
        """

    @abstractmethod
    def vaciar(self):
        """Espera que no queden envíos pendientes de confirmación."""

    @abstractmethod
    def cerrar(self):
        """Libera estado del canal sin cerrar el socket UDP compartido."""
