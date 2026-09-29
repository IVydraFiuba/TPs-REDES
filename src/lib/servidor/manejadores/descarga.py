"""Operación de descarga del servidor."""

import logging
import threading

from lib.capas.pca import (
    ErrorRespuesta,
    Mensaje,
    TipoMensaje,
    aceptado,
)
from lib.constantes import TAMANIO_BLOQUE

logger = logging.getLogger(__name__)


def manejador_descarga(comunicador, almacenamiento, nombre):
    """Envía al cliente un archivo del almacenamiento."""
    _, tamanio = almacenamiento.obtener_info_descarga(nombre)
    logger.info(
        "[%s] Iniciando descarga: %s (%d bytes)",
        threading.current_thread().name,
        nombre,
        tamanio
    )
    with almacenamiento.abrir_descarga(nombre) as lector:
        comunicador.enviar(aceptado(tamanio))
        while bloque := lector.leer_bloque(TAMANIO_BLOQUE):
            comunicador.enviar(
                Mensaje(TipoMensaje.BLOQUE_ARCHIVO, bloque)
            )
        comunicador.enviar(Mensaje(TipoMensaje.FIN_ARCHIVO))
        comunicador.vaciar()
        mensaje = comunicador.recibir()
        if mensaje.tipo != TipoMensaje.COMPLETADO or mensaje.carga:
            raise ErrorRespuesta("Confirmación de descarga inesperada")
        logger.info("Descarga completada: %s (%d bytes)", nombre, tamanio)
