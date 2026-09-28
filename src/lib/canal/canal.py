"""Interfaz abstracta para canales de transporte.

Cada implementación (UDP directo, Stop&Wait, SACK) cumple este contrato.
"""

from abc import ABC, abstractmethod


class Canal(ABC):
    """Canal de transporte abstracto.

    Contrato:
        - enviar(bytes): envía datos al peer
        - recibir() -> (bytes, direccion): recibe datos del peer
        - cerrar(): cierra el canal ordenadamente
    """

    @abstractmethod
    def enviar(self, datos):
        """Envía datos al peer.

        Args:
            datos: bytes a enviar
        """

    @abstractmethod
    def recibir(self):
        """Recibe datos del peer.

        Returns:
            tuple: (datos: bytes, direccion: tuple)
        """

    def cerrar(self):
        """Cierra el canal ordenadamente."""
