"""Canal UDP directo sin confiabilidad.

MODO MOCK TEMPORAL - No implementa ningún mecanismo de RDT.
Este módulo será reemplazado cuando se implementen los protocolos
Stop&Wait y SACK para el trabajo práctico.

Solo debe usarse para pruebas de integración del protocolo de aplicación.
"""

import socket

from lib.constantes import TAMANIO_MAX_DATAGRAMA, TIMEOUT_CLIENTE
from lib.protocolo.errores import ErrorComunicacion, ErrorTiempoEspera

from .canal import Canal


class CanalUdpDirecto(Canal):
    """Canal UDP que no provee confiabilidad.

    Interfaz:
        - enviar(bytes): envía datos crudos al peer
        - recibir() -> (bytes, direccion): recibe datos crudos del peer
        - cerrar(): cierra el canal
    """

    def __init__(self, conexion, direccion):
        self._conexion = conexion
        self._direccion = direccion

    def enviar(self, datos):
        """Envía datos crudos al peer.

        Args:
            datos: bytes a enviar
        """
        try:
            self._conexion.sendto(datos, self._direccion)
        except OSError as e:
            raise ErrorComunicacion(f"Error al enviar: {e}") from e

    def recibir(self):
        """Recibe datos crudos del peer.

        Returns:
            tuple: (datos: bytes, direccion: tuple)

        Raises:
            ErrorTiempoEspera: si se agota el timeout
            ErrorComunicacion: si hay error de red
        """
        try:
            self._conexion.settimeout(TIMEOUT_CLIENTE)
            datos, direccion = self._conexion.recvfrom(TAMANIO_MAX_DATAGRAMA)
        except socket.timeout:
            raise ErrorTiempoEspera("Tiempo de espera agotado")
        except OSError as e:
            raise ErrorComunicacion(f"Error al recibir: {e}") from e

        return datos, direccion

    def cerrar(self):
        """Cierra el canal."""
        try:
            self._conexion.close()
        except OSError:
            pass
