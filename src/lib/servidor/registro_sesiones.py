"""Registro de sesiones activas identificadas por el endpoint del cliente."""

import logging
import threading
import time
from dataclasses import dataclass

from lib.constantes import ESPERA_TIME_WAIT

logger = logging.getLogger(__name__)


@dataclass
class EntradaSesion:
    protocolo: int
    enlace: object
    respuesta_syn: bytes
    hilo: object = None


class RegistroSesiones:
    """Sesiones activas, mas las recien cerradas que siguen en espera.

    Una sesion cerrada deja su ultimo ACK anotado durante
    ESPERA_TIME_WAIT. Si el par retransmite el ultimo mensaje porque no
    le llego ese ACK, el despachador lo contesta desde aca: no hace
    falta ningun hilo ni ninguna marca de "mensaje final" en el canal,
    porque reenviar el ultimo ACK es la respuesta correcta a cualquier
    retransmision de lo ultimo que se recibio.
    """

    def __init__(self, maximo):
        self._maximo = maximo
        self._sesiones = {}
        self._en_espera = {}
        self._cerrojo = threading.Lock()

    def buscar(self, direccion):
        with self._cerrojo:
            return self._sesiones.get(direccion)

    def agregar(self, direccion, entrada):
        """Reserva una dirección sin reemplazar una sesión activa."""
        with self._cerrojo:
            if (direccion in self._sesiones
                    or len(self._sesiones) >= self._maximo):
                return False
            self._sesiones[direccion] = entrada
            logger.info("Sesion agregada: %s (total: %d)", direccion, len(self._sesiones))
            return True

    def quitar(self, direccion):
        """Saca la sesion y deja su ultimo ACK a mano por un rato."""
        with self._cerrojo:
            resultado = self._sesiones.pop(direccion, None)
            if resultado is not None:
                logger.info("Sesion removida: %s (total: %d)", direccion, len(self._sesiones))
                self._purgar(time.monotonic())
                ultimo = resultado.enlace.ultimo_enviado
                if ultimo is not None:
                    self._en_espera[direccion] = (
                        ultimo, time.monotonic() + ESPERA_TIME_WAIT
                    )
            return resultado

    def _purgar(self, ahora):
        """Descarta las esperas vencidas. Se llama con el cerrojo tomado."""
        for direccion in [clave for clave, (_, vence)
                          in self._en_espera.items() if vence <= ahora]:
            del self._en_espera[direccion]

    def respuesta_en_espera(self, direccion):
        """Ultimo ACK de una sesion cerrada hace poco, o None."""
        ahora = time.monotonic()
        with self._cerrojo:
            self._purgar(ahora)
            espera = self._en_espera.get(direccion)
            return None if espera is None else espera[0]

    def interrumpir_todas(self):
        with self._cerrojo:
            entradas = list(self._sesiones.values())
        for entrada in entradas:
            entrada.enlace.interrumpir()
        return [
            entrada.hilo
            for entrada in entradas
            if entrada.hilo is not None
        ]
