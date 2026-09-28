"""Canal SACK - stub no implementado.

Este módulo será implementado cuando se diseñe el protocolo
de transporte confiable con Selective ACK para el trabajo práctico.
"""

from lib.protocolo.errores import ErrorModoNoImplementado

from .canal import Canal


class CanalSack(Canal):
    """Canal de transporte confiable con SACK.

    No implementado aún.
    """

    def __init__(self, conexion, direccion):
        self._conexion = conexion
        self._direccion = direccion

    def enviar(self, datos):
        """Envía datos de forma confiable con SACK."""
        raise ErrorModoNoImplementado(
            "Canal SACK no implementado. "
            "Usar PROTO_DIRECTO para pruebas."
        )

    def recibir(self):
        """Recibe datos de forma confiable con SACK."""
        raise ErrorModoNoImplementado(
            "Canal SACK no implementado. "
            "Usar PROTO_DIRECTO para pruebas."
        )

    def cerrar(self):
        """Cierra el canal."""

