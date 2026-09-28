"""Interfaz que consume la aplicación; no expone direcciones ni ACK."""

from abc import ABC, abstractmethod


class Canal(ABC):
    @abstractmethod
    def enviar(self, datos: bytes):
        """Admite un mensaje completo en el canal."""

    @abstractmethod
    def recibir(self) -> bytes:
        """Devuelve un mensaje completo del par."""

    @abstractmethod
    def vaciar(self):
        """Espera confirmación de todos los envíos pendientes."""

    @abstractmethod
    def cerrar(self):
        """Libera recursos propios, sin cerrar sockets compartidos."""
