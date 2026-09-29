"""Operación de descarga del cliente."""

import logging

from lib.archivos.archivos_cliente import preparar_destino_descarga
from lib.capas.pca import (
    ErrorRespuesta,
    ErrorTransferenciaIncompleta,
    Mensaje,
    TipoMensaje,
    leer_tamanio_aceptado,
    solicitud_descarga,
)

logger = logging.getLogger(__name__)


def manejador_descarga(comunicador, destino, nombre):
    """Recibe un archivo del servidor mediante mensajes de aplicación."""
    comunicador.enviar(solicitud_descarga(nombre))
    respuesta = comunicador.esperar(
        TipoMensaje.ACEPTADO,
        con_carga=True,
    )
    tamanio = leer_tamanio_aceptado(respuesta)
    with preparar_destino_descarga(destino) as escritor:
        recibidos = 0
        while True:
            mensaje = comunicador.recibir_respuesta()
            if mensaje.tipo == TipoMensaje.BLOQUE_ARCHIVO:
                recibidos += len(mensaje.carga)
                if recibidos > tamanio:
                    raise ErrorTransferenciaIncompleta(
                        "Datos exceden el tamaño anunciado"
                    )
                escritor.escribir_bloque(mensaje.carga)
            elif (mensaje.tipo == TipoMensaje.FIN_ARCHIVO
                  and not mensaje.carga):
                if recibidos != tamanio:
                    raise ErrorTransferenciaIncompleta(
                        f"Se esperaban {tamanio} bytes y "
                        f"llegaron {recibidos}"
                    )
                escritor.confirmar()
                comunicador.enviar(Mensaje(TipoMensaje.COMPLETADO))
                comunicador.vaciar()
                logger.info(
                    "Descarga completada: %s (%d bytes)",
                    nombre,
                    recibidos,
                )
                return
            else:
                raise ErrorRespuesta(
                    f"Mensaje inesperado: {mensaje.tipo.name}"
                )
