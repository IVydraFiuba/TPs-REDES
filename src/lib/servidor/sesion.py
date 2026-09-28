"""Una solicitud y una transferencia por sesión; ejecutada en el mismo hilo."""

import logging

from lib.archivos.errores_archivos import ErrorArchivo
from lib.constantes import TAMANIO_BLOQUE
from lib.protocolo_aplicacion import (
    ErrorMensaje,
    ErrorRespuesta,
    ErrorTransferenciaIncompleta,
    aceptado,
    codificar_mensaje,
    decodificar_mensaje,
    error_remoto,
    leer_solicitud_descarga,
    leer_solicitud_subida,
)
from lib.protocolo_aplicacion.mensaje import Mensaje, TipoMensaje
from lib.rdt.errores import ErrorSegmento
from lib.udp.errores import ErrorComunicacion

logger = logging.getLogger(__name__)


class SesionServidor:
    def __init__(self, canal, almacenamiento):
        self._canal = canal
        self._almacenamiento = almacenamiento

    def _enviar(self, mensaje):
        self._canal.enviar(codificar_mensaje(mensaje))

    def _recibir(self):
        return decodificar_mensaje(self._canal.recibir())

    def ejecutar(self):
        try:
            mensaje = self._recibir()
            if mensaje.tipo == TipoMensaje.SOLICITUD_SUBIDA:
                nombre, tamanio = leer_solicitud_subida(mensaje)
                self._subir(nombre, tamanio)
            elif mensaje.tipo == TipoMensaje.SOLICITUD_DESCARGA:
                self._descargar(leer_solicitud_descarga(mensaje))
            else:
                raise ErrorRespuesta(f"Solicitud inesperada: {mensaje.tipo.name}")
        except (ErrorArchivo, ErrorMensaje) as error:
            logger.warning("Error de operación: %s", error)
            try:
                self._enviar(error_remoto(type(error).__name__, str(error)))
                self._canal.vaciar()
            except (ErrorComunicacion, ErrorSegmento):
                logger.warning("No se pudo informar el error remoto")
        except (ErrorComunicacion, ErrorSegmento) as error:
            logger.warning("Sesión interrumpida: %s", error)
        finally:
            self._canal.cerrar()

    def _subir(self, nombre, tamanio):
        with self._almacenamiento.recibir_subida(nombre) as escritor:
            self._enviar(aceptado())
            recibidos = 0
            while True:
                mensaje = self._recibir()
                if mensaje.tipo == TipoMensaje.BLOQUE_ARCHIVO:
                    recibidos += len(mensaje.carga)
                    if recibidos > tamanio:
                        raise ErrorTransferenciaIncompleta("Datos exceden el tamaño anunciado")
                    escritor.escribir_bloque(mensaje.carga)
                elif mensaje.tipo == TipoMensaje.FIN_ARCHIVO and not mensaje.carga:
                    if recibidos != tamanio:
                        raise ErrorTransferenciaIncompleta(
                            f"Se esperaban {tamanio} bytes y llegaron {recibidos}")
                    escritor.confirmar()
                    self._enviar(Mensaje(TipoMensaje.COMPLETADO))
                    self._canal.vaciar()
                    logger.info("Subida completada: %s (%d bytes)", nombre, recibidos)
                    return
                else:
                    raise ErrorRespuesta(f"Mensaje inesperado: {mensaje.tipo.name}")

    def _descargar(self, nombre):
        _, tamanio = self._almacenamiento.obtener_info_descarga(nombre)
        with self._almacenamiento.abrir_descarga(nombre) as lector:
            self._enviar(aceptado(tamanio))
            while bloque := lector.leer_bloque(TAMANIO_BLOQUE):
                self._enviar(Mensaje(TipoMensaje.BLOQUE_ARCHIVO, bloque))
            self._enviar(Mensaje(TipoMensaje.FIN_ARCHIVO))
            self._canal.vaciar()
            mensaje = self._recibir()
            if mensaje.tipo != TipoMensaje.COMPLETADO or mensaje.carga:
                raise ErrorRespuesta("Confirmación de descarga inesperada")
            logger.info("Descarga completada: %s (%d bytes)", nombre, tamanio)
