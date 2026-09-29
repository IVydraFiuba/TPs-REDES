"""Contrato de datagramas utilizado por los canales RDT."""

from abc import ABC, abstractmethod


class Enlace(ABC):
    @abstractmethod
    def enviar(self, datos: bytes):
        """Envía un datagrama al otro extremo."""

    @abstractmethod
    def recibir(self, timeout=None) -> bytes:
        """Recibe un datagrama o vence luego de `timeout` segundos.

        Si `timeout` es None, el enlace usa el plazo de inactividad general.
        Los canales confiables podrán pasar su propio RTO sin conocer si el
        enlace lee un socket de cliente o la cola de una sesión del servidor.
        """
