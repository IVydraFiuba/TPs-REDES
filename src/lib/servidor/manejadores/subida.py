"""Operación de subida del servidor."""

import logging

from lib.protocolo_aplicacion import (
    ErrorRespuesta,
    ErrorTransferenciaIncompleta,
    Mensaje,
    TipoMensaje,
    aceptado,
)

logger = logging.getLogger(__name__)


def manejador_subida(comunicador, almacenamiento, nombre, tamanio):
    """Recibe un archivo y lo publica cuando llega completo."""
    with almacenamiento.recibir_subida(nombre) as escritor:
        comunicador.enviar(aceptado())
        recibidos = 0
        while True:
            mensaje = comunicador.recibir()
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
                    "Subida completada: %s (%d bytes)",
                    nombre,
                    recibidos,
                )
                return
            else:
                raise ErrorRespuesta(
                    f"Mensaje inesperado: {mensaje.tipo.name}"
                )
