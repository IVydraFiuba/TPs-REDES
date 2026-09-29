"""Contrato de datagramas utilizado por los canales RDT."""

from abc import ABC, abstractmethod


class Enlace(ABC):
    @abstractmethod
    def enviar(self, datos: bytes):
        """Envía un datagrama al otro extremo."""

    @abstractmethod
    def recibir(self) -> bytes:
        """Recibe un datagrama del otro extremo."""
