"""Manejador de subida de archivos."""

import logging

from lib.archivos.archivos_cliente import abrir_origen_subida
from lib.constantes import TAMANIO_BLOQUE
from lib.protocolo_aplicacion import (
    ErrorRespuesta,
    Mensaje,
    TipoMensaje,
    codificar_mensaje,
    decodificar_mensaje,
    solicitud_subida,
)

logger = logging.getLogger(__name__)


def manejador_subida(canal, origen, nombre):
    """Envía un archivo al servidor usando el canal dado."""
    with abrir_origen_subida(origen) as lector:
        tamanio = lector.ruta.stat().st_size
        _enviar(canal, solicitud_subida(nombre, tamanio))
        _esperar(canal, TipoMensaje.ACEPTADO)
        while bloque := lector.leer_bloque(TAMANIO_BLOQUE):
            _enviar(canal, Mensaje(TipoMensaje.BLOQUE_ARCHIVO, bloque))
        _enviar(canal, Mensaje(TipoMensaje.FIN_ARCHIVO))
        canal.vaciar()
        _esperar(canal, TipoMensaje.COMPLETADO)
        logger.info("Subida completada: %s (%d bytes)", nombre, tamanio)


def _enviar(canal, mensaje):
    canal.enviar(codificar_mensaje(mensaje))


def _recibir(canal):
    mensaje = decodificar_mensaje(canal.recibir())
    if mensaje.tipo == TipoMensaje.ERROR:
        from lib.protocolo_aplicacion import leer_error
        codigo, detalle = leer_error(mensaje)
        from lib.protocolo_aplicacion import ErrorOperacionRemota
        raise ErrorOperacionRemota(f"{codigo}: {detalle}")
    return mensaje


def _esperar(canal, tipo):
    mensaje = _recibir(canal)
    if mensaje.tipo != tipo or mensaje.carga:
        raise ErrorRespuesta(f"Se esperaba {tipo.name}, llegó {mensaje.tipo.name}")
