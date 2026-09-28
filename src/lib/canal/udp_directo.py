"""Canal UDP directo sin confiabilidad.

MODO MOCK TEMPORAL - No implementa ningún mecanismo de RDT.
Este módulo será reemplazado cuando se implementen los protocolos
Stop&Wait y SACK para el trabajo práctico.

Solo debe usarse para pruebas de integración del protocolo de aplicación.
"""

import socket

from lib.constantes import TAMANIO_MAX_DATAGRAMA, TIMEOUT_CLIENTE
from lib.protocolo.errores import (
    ErrorComunicacion,
    ErrorServidorOcupado,
    ErrorTiempoEspera,
)
from lib.protocolo.mensajes import codificar_mensaje, decodificar_mensaje


class CanalUdpDirecto:
    """Canal UDP que no provee confiabilidad."""

    def __init__(self, conexion, direccion):
        self._conexion = conexion
        self._direccion = direccion

    def enviar(self, tipo, carga=b""):
        """Envía un mensaje codificado."""
        try:
            self._conexion.sendto(
                codificar_mensaje(tipo, carga),
                self._direccion
            )
        except OSError as e:
            raise ErrorComunicacion(f"Error al enviar: {e}") from e

    def enviar_datagrama(self, datagrama):
        """Envía un datagrama raw."""
        try:
            self._conexion.sendto(datagrama, self._direccion)
        except OSError as e:
            raise ErrorComunicacion(f"Error al enviar datagrama: {e}") from e

    def recibir(self):
        """Recibe un mensaje. Verifica que venga del cliente esperado."""
        try:
            self._conexion.settimeout(TIMEOUT_CLIENTE)
            datagrama, direccion = self._conexion.recvfrom(TAMANIO_MAX_DATAGRAMA)
        except socket.timeout:
            raise ErrorTiempoEspera("Tiempo de espera agotado")
        except OSError as e:
            raise ErrorComunicacion(f"Error al recibir: {e}") from e

        if direccion != self._direccion:
            raise ErrorServidorOcupado(
                f"Mensaje de origen inesperado: {direccion}"
            )

        return decodificar_mensaje(datagrama)
