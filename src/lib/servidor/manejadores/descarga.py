"""Operación de descarga del servidor."""

import logging

from lib.constantes import TAMANIO_BLOQUE
from lib.protocolo_aplicacion import (
    ErrorRespuesta,
    Mensaje,
    TipoMensaje,
    aceptado,
)

logger = logging.getLogger(__name__)


def manejador_descarga(comunicador, almacenamiento, nombre):
    """Envía al cliente un archivo del almacenamiento."""
    _, tamanio = almacenamiento.obtener_info_descarga(nombre)
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
