"""Manejador de descarga de archivos."""

import logging

from lib.archivos.archivos_cliente import preparar_destino_descarga
from lib.protocolo_aplicacion import (
    ErrorOperacionRemota,
    ErrorRespuesta,
    ErrorTransferenciaIncompleta,
    Mensaje,
    TipoMensaje,
    codificar_mensaje,
    decodificar_mensaje,
    leer_error,
    leer_tamanio_aceptado,
    solicitud_descarga,
)

logger = logging.getLogger(__name__)


def manejador_descarga(canal, destino, nombre):
    """Descarga un archivo del servidor usando el canal dado."""
    _enviar(canal, solicitud_descarga(nombre))
    respuesta = _esperar(canal, TipoMensaje.ACEPTADO, con_carga=True)
    tamanio = leer_tamanio_aceptado(respuesta)
    with preparar_destino_descarga(destino) as escritor:
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
                logger.info("Descarga completada: %s (%d bytes)", nombre, recibidos)
                return
            else:
                raise ErrorRespuesta(f"Mensaje inesperado: {mensaje.tipo.name}")


def _enviar(canal, mensaje):
    canal.enviar(codificar_mensaje(mensaje))


def _recibir(canal):
    mensaje = decodificar_mensaje(canal.recibir())
    if mensaje.tipo == TipoMensaje.ERROR:
        codigo, detalle = leer_error(mensaje)
        raise ErrorOperacionRemota(f"{codigo}: {detalle}")
    return mensaje


def _esperar(canal, tipo, con_carga=False):
    mensaje = _recibir(canal)
    if mensaje.tipo != tipo or (not con_carga and mensaje.carga):
        raise ErrorRespuesta(f"Se esperaba {tipo.name}, llegó {mensaje.tipo.name}")
    return mensaje
