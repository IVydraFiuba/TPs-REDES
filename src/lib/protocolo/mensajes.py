"""Tipos y codificación de mensajes del protocolo de aplicación."""

import json
import struct

from lib.constantes import TAMANIO_BLOQUE, TAMANIO_MAX_DATAGRAMA

from .errores import ErrorMensaje

_TIPOS = {
    "SOLICITUD_UPLOAD": 1,
    "ACEPTADO": 2,
    "DATOS": 3,
    "FIN": 4,
    "COMPLETADO": 5,
    "ERROR": 6,
}

_TIPOS_CODIGO = {codigo: nombre for nombre, codigo in _TIPOS.items()}

_CABECERA = struct.Struct("!BH")


def codificar_mensaje(tipo, carga=b""):
    """Codifica un mensaje con cabecera de 3 bytes."""
    if tipo not in _TIPOS:
        raise ErrorMensaje(f"Tipo de mensaje desconocido: {tipo}")
    return _CABECERA.pack(_TIPOS[tipo], len(carga)) + carga


def decodificar_mensaje(datagrama):
    """Decodifica un mensaje. Retorna (nombre_tipo, carga)."""
    if len(datagrama) < 3:
        raise ErrorMensaje("Datagrama demasiado corto")
    tipo_codigo, longitud = _CABECERA.unpack(datagrama[:3])
    if len(datagrama) - 3 != longitud:
        raise ErrorMensaje(
            f"Longitud不一致: cabecera={longitud}, real={len(datagrama) - 3}"
        )
    tipo_nombre = _TIPOS_CODIGO.get(tipo_codigo)
    if tipo_nombre is None:
        raise ErrorMensaje(f"Código de tipo desconocido: {tipo_codigo}")
    return tipo_nombre, datagrama[3:]


def codificar_solicitud(nombre, tamanio, modo="directo"):
    """Codifica metadata de solicitud como JSON."""
    return json.dumps(
        {"nombre": nombre, "tamanio": tamanio, "modo": modo},
        ensure_ascii=False
    ).encode("utf-8")


def decodificar_solicitud(carga):
    """Decodifica metadata de solicitud. Retorna (nombre, tamanio)."""
    try:
        datos = json.loads(carga.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise ErrorMensaje(f"Solicitud con JSON inválido: {e}")
    if "nombre" not in datos or "tamanio" not in datos:
        raise ErrorMensaje("Solicitud faltan campos obligatorios")
    return datos["nombre"], datos["tamanio"]


def codificar_error(codigo, detalle):
    """Codifica un mensaje de error como JSON."""
    return json.dumps(
        {"codigo": codigo, "detalle": detalle},
        ensure_ascii=False
    ).encode("utf-8")


def decodificar_error(carga):
    """Decodifica mensaje de error. Retorna (codigo, detalle)."""
    try:
        datos = json.loads(carga.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise ErrorMensaje(f"Error con JSON inválido: {e}")
    if "codigo" not in datos or "detalle" not in datos:
        raise ErrorMensaje("Error faltan campos obligatorios")
    return datos["codigo"], datos["detalle"]
