"""Ciclo de vida de una operación ejecutada en un hilo de sesión."""

import logging
import threading

from lib.archivos.errores_archivos import ErrorArchivo
from lib.capas.pca import (
    ComunicadorAplicacion,
    ErrorMensaje,
    ErrorRespuesta,
    TipoMensaje,
    error_remoto,
    leer_solicitud_descarga,
    leer_solicitud_subida,
)
from lib.capas.rdt.errores import ErrorSegmento
from lib.capas.udp.errores import ErrorComunicacion

from .manejadores import manejador_descarga, manejador_subida

logger = logging.getLogger(__name__)


class SesionServidor:
    def __init__(self, canal, almacenamiento):
        self._canal = canal
        self._comunicador = ComunicadorAplicacion(canal)
        self._almacenamiento = almacenamiento

    def ejecutar(self):
        try:
            logger.info(
                "[%s] Sesion iniciada",
                threading.current_thread().name
            )
            mensaje = self._comunicador.recibir()
            logger.debug(
                "[%s] Mensaje recibido: %s",
                threading.current_thread().name,
                mensaje.tipo.name
            )
            if mensaje.tipo == TipoMensaje.SOLICITUD_SUBIDA:
                nombre, tamanio = leer_solicitud_subida(mensaje)
                logger.info(
                    "[%s] Handler: subida %s (%d bytes)",
                    threading.current_thread().name,
                    nombre,
                    tamanio
                )
                manejador_subida(
                    self._comunicador,
                    self._almacenamiento,
                    nombre,
                    tamanio,
                )
            elif mensaje.tipo == TipoMensaje.SOLICITUD_DESCARGA:
                nombre = leer_solicitud_descarga(mensaje)
                logger.info(
                    "[%s] Handler: descarga %s",
                    threading.current_thread().name,
                    nombre
                )
                manejador_descarga(
                    self._comunicador,
                    self._almacenamiento,
                    nombre,
                )
            else:
                raise ErrorRespuesta(
                    f"Solicitud inesperada: {mensaje.tipo.name}"
                )
        except (ErrorArchivo, ErrorMensaje) as error:
            logger.warning("[%s] Error de operacion: %s", threading.current_thread().name, error)
            try:
                self._comunicador.enviar(
                    error_remoto(type(error).__name__, str(error))
                )
                self._comunicador.vaciar()
            except (ErrorComunicacion, ErrorSegmento):
                logger.warning("[%s] No se pudo informar el error remoto", threading.current_thread().name)
        except (ErrorComunicacion, ErrorSegmento) as error:
            logger.warning("[%s] Sesion interrumpida: %s", threading.current_thread().name, error)
        finally:
            self._canal.cerrar()
            logger.info("[%s] Sesion cerrada", threading.current_thread().name)
