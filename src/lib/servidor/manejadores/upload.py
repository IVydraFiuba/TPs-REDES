"""Manejador de subida en el servidor."""

import logging

from lib.protocolo_aplicacion import (
    ErrorRespuesta,
    ErrorTransferenciaIncompleta,
    Mensaje,
    TipoMensaje,
    aceptado,
    codificar_mensaje,
    decodificar_mensaje,
)

logger = logging.getLogger(__name__)


def manejador_subida(canal, almacenamiento, nombre, tamanio):
    """Recibe un archivo del cliente y lo guarda en el almacenamiento."""
    with almacenamiento.recibir_subida(nombre) as escritor:
        _enviar(canal, aceptado())
        recibidos = 0
        while True:
            mensaje = _recibir(canal)
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
                _enviar(canal, Mensaje(TipoMensaje.COMPLETADO))
                canal.vaciar()
                logger.info("Subida completada: %s (%d bytes)", nombre, recibidos)
                return
            else:
                raise ErrorRespuesta(f"Mensaje inesperado: {mensaje.tipo.name}")


def _enviar(canal, mensaje):
    canal.enviar(codificar_mensaje(mensaje))


def _recibir(canal):
    return decodificar_mensaje(canal.recibir())
