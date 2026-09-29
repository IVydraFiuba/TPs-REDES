"""Registro de sesiones activas identificadas por el endpoint del cliente."""

import threading
from dataclasses import dataclass


@dataclass
class EntradaSesion:
    protocolo: int
    enlace: object
    respuesta_syn: bytes
    hilo: object = None


class RegistroSesiones:
    def __init__(self, maximo):
        self._maximo = maximo
        self._sesiones = {}
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
            return True

    def quitar(self, direccion):
        with self._cerrojo:
            return self._sesiones.pop(direccion, None)

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
