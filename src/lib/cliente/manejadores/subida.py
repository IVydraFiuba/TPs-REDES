"""Operación de subida del cliente."""

import logging

from lib.archivos.archivos_cliente import abrir_origen_subida
from lib.capas.pca import Mensaje, TipoMensaje, solicitud_subida
from lib.constantes import TAMANIO_BLOQUE

logger = logging.getLogger(__name__)


def manejador_subida(comunicador, origen, nombre):
    """Envía un archivo al servidor mediante mensajes de aplicación."""
    with abrir_origen_subida(origen) as lector:
        tamanio = lector.ruta.stat().st_size
        comunicador.enviar(solicitud_subida(nombre, tamanio))
        comunicador.esperar(TipoMensaje.ACEPTADO)
        while bloque := lector.leer_bloque(TAMANIO_BLOQUE):
            comunicador.enviar(
                Mensaje(TipoMensaje.BLOQUE_ARCHIVO, bloque)
            )
        comunicador.enviar(Mensaje(TipoMensaje.FIN_ARCHIVO))
        comunicador.vaciar()
        comunicador.esperar(TipoMensaje.COMPLETADO)
        logger.info("Subida completada: %s (%d bytes)", nombre, tamanio)
