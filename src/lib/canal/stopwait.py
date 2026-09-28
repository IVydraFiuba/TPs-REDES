"""Canal Stop&Wait - stub no implementado.

Este módulo será implementado cuando se diseñe el protocolo
de transporte confiable Stop&Wait para el trabajo práctico.
"""

from lib.protocolo.errores import ErrorModoNoImplementado

from .canal import Canal


class CanalStopWait(Canal):
    """Canal de transporte confiable con Stop & Wait.

    No implementado aún.
    """

    def __init__(self, conexion, direccion):
        self._conexion = conexion
        self._direccion = direccion

    def enviar(self, datos):
        """Envía datos de forma confiable con Stop&Wait."""
        raise ErrorModoNoImplementado(
            "Canal Stop&Wait no implementado. "
            "Usar PROTO_DIRECTO para pruebas."
        )

    def recibir(self):
        """Recibe datos de forma confiable con Stop&Wait."""
        raise ErrorModoNoImplementado(
            "Canal Stop&Wait no implementado. "
            "Usar PROTO_DIRECTO para pruebas."
        )

    def cerrar(self):
        """Cierra el canal."""
