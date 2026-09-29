"""Comunica mensajes de aplicación sobre un canal RDT de bytes."""

import logging
import threading

from .codificacion import codificar_mensaje, decodificar_mensaje, leer_error
from .errores import ErrorOperacionRemota, ErrorRespuesta
from .mensaje import TipoMensaje

logger = logging.getLogger(__name__)


class ComunicadorAplicacion:
    def __init__(self, canal):
        self._canal = canal

    def enviar(self, mensaje):
        logger.debug(
            "[%s] Enviando mensaje PCA: %s",
            threading.current_thread().name,
            mensaje.tipo.name if hasattr(mensaje, 'tipo') else type(mensaje).__name__
        )
        self._canal.enviar(codificar_mensaje(mensaje))

    def recibir(self):
        logger.debug(
            "[%s] Recibiendo mensaje PCA",
            threading.current_thread().name
        )
        return decodificar_mensaje(self._canal.recibir())

    def recibir_respuesta(self):
        mensaje = self.recibir()
        if mensaje.tipo == TipoMensaje.ERROR:
            codigo, detalle = leer_error(mensaje)
            raise ErrorOperacionRemota(f"{codigo}: {detalle}")
        return mensaje

    def esperar(self, tipo, con_carga=False):
        mensaje = self.recibir_respuesta()
        if mensaje.tipo != tipo or (not con_carga and mensaje.carga):
            raise ErrorRespuesta(
                f"Se esperaba {tipo.name}, llegó {mensaje.tipo.name}"
            )
        return mensaje

    def vaciar(self):
        self._canal.vaciar()
