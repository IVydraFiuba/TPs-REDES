"""Ciclo de vida de una operación ejecutada en un hilo de sesión."""

import logging

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
            mensaje = self._comunicador.recibir()
            if mensaje.tipo == TipoMensaje.SOLICITUD_SUBIDA:
                nombre, tamanio = leer_solicitud_subida(mensaje)
                manejador_subida(
                    self._comunicador,
                    self._almacenamiento,
                    nombre,
                    tamanio,
                )
            elif mensaje.tipo == TipoMensaje.SOLICITUD_DESCARGA:
                manejador_descarga(
                    self._comunicador,
                    self._almacenamiento,
                    leer_solicitud_descarga(mensaje),
                )
            else:
                raise ErrorRespuesta(
                    f"Solicitud inesperada: {mensaje.tipo.name}"
                )
        except (ErrorArchivo, ErrorMensaje) as error:
            logger.warning("Error de operación: %s", error)
            try:
                self._comunicador.enviar(
                    error_remoto(type(error).__name__, str(error))
                )
                self._comunicador.vaciar()
            except (ErrorComunicacion, ErrorSegmento):
                logger.warning("No se pudo informar el error remoto")
        except (ErrorComunicacion, ErrorSegmento) as error:
            logger.warning("Sesión interrumpida: %s", error)
        finally:
            self._canal.cerrar()
