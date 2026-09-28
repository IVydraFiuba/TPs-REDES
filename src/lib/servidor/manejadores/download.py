"""Manejador de descarga en el servidor."""

import logging

from lib.constantes import TAMANIO_BLOQUE
from lib.protocolo_aplicacion import (
    ErrorRespuesta,
    Mensaje,
    TipoMensaje,
    aceptado,
    codificar_mensaje,
    decodificar_mensaje,
)

logger = logging.getLogger(__name__)


def manejador_descarga(canal, almacenamiento, nombre):
    """Envía un archivo al cliente desde el almacenamiento."""
    _, tamanio = almacenamiento.obtener_info_descarga(nombre)
    with almacenamiento.abrir_descarga(nombre) as lector:
        _enviar(canal, aceptado(tamanio))
        while bloque := lector.leer_bloque(TAMANIO_BLOQUE):
            _enviar(canal, Mensaje(TipoMensaje.BLOQUE_ARCHIVO, bloque))
        _enviar(canal, Mensaje(TipoMensaje.FIN_ARCHIVO))
        canal.vaciar()
        mensaje = _recibir(canal)
        if mensaje.tipo != TipoMensaje.COMPLETADO or mensaje.carga:
            raise ErrorRespuesta("Confirmación de descarga inesperada")
        logger.info("Descarga completada: %s (%d bytes)", nombre, tamanio)


def _enviar(canal, mensaje):
    canal.enviar(codificar_mensaje(mensaje))


def _recibir(canal):
    return decodificar_mensaje(canal.recibir())
