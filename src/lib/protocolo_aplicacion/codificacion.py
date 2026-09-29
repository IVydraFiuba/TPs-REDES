"""Único lugar que conoce los formatos binarios y JSON de aplicación."""

import json
import struct

from lib.constantes import TAMANIO_MAX_CARGA_SEGMENTO

from .errores import ErrorMensaje
from .mensaje import Mensaje, TipoMensaje

_CABECERA = struct.Struct("!BH")


def codificar_mensaje(mensaje):
    if (not isinstance(mensaje, Mensaje)
            or not isinstance(mensaje.tipo, TipoMensaje)):
        raise ErrorMensaje("Mensaje inválido")
    if not isinstance(mensaje.carga, bytes):
        raise ErrorMensaje("La carga debe ser bytes")
    if len(mensaje.carga) + _CABECERA.size > TAMANIO_MAX_CARGA_SEGMENTO:
        raise ErrorMensaje("El mensaje supera el tamaño del segmento")
    return _CABECERA.pack(mensaje.tipo, len(mensaje.carga)) + mensaje.carga


def decodificar_mensaje(datos):
    if len(datos) < _CABECERA.size or len(datos) > TAMANIO_MAX_CARGA_SEGMENTO:
        raise ErrorMensaje("Tamaño de mensaje inválido")
    tipo, longitud = _CABECERA.unpack_from(datos)
    if len(datos) != _CABECERA.size + longitud:
        raise ErrorMensaje(
            "La longitud del mensaje no coincide con la cabecera"
        )
    try:
        return Mensaje(TipoMensaje(tipo), datos[_CABECERA.size:])
    except ValueError as error:
        raise ErrorMensaje(f"Tipo de mensaje desconocido: {tipo}") from error


def _codificar_json(datos):
    return json.dumps(datos, ensure_ascii=False).encode("utf-8")


def _decodificar_json(carga):
    try:
        datos = json.loads(carga.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise ErrorMensaje("JSON inválido") from error
    if not isinstance(datos, dict):
        raise ErrorMensaje("Se esperaba un objeto JSON")
    return datos


def _nombre(datos):
    nombre = datos.get("nombre")
    if not isinstance(nombre, str) or not nombre:
        raise ErrorMensaje("Nombre de archivo inválido")
    return nombre


def _tamanio(datos):
    tamanio = datos.get("tamanio")
    if type(tamanio) is not int or tamanio < 0:
        raise ErrorMensaje("Tamaño de archivo inválido")
    return tamanio


def solicitud_subida(nombre, tamanio):
    return Mensaje(TipoMensaje.SOLICITUD_SUBIDA,
                   _codificar_json({"nombre": nombre, "tamanio": tamanio}))


def leer_solicitud_subida(mensaje):
    datos = _decodificar_json(mensaje.carga)
    return _nombre(datos), _tamanio(datos)


def solicitud_descarga(nombre):
    return Mensaje(
        TipoMensaje.SOLICITUD_DESCARGA,
        _codificar_json({"nombre": nombre}),
    )


def leer_solicitud_descarga(mensaje):
    return _nombre(_decodificar_json(mensaje.carga))


def aceptado(tamanio=None):
    carga = b"" if tamanio is None else _codificar_json({"tamanio": tamanio})
    return Mensaje(TipoMensaje.ACEPTADO, carga)


def leer_tamanio_aceptado(mensaje):
    return _tamanio(_decodificar_json(mensaje.carga))


def error_remoto(codigo, detalle):
    return Mensaje(TipoMensaje.ERROR,
                   _codificar_json({"codigo": codigo, "detalle": detalle}))


def leer_error(mensaje):
    datos = _decodificar_json(mensaje.carga)
    if not all(isinstance(datos.get(k), str) for k in ("codigo", "detalle")):
        raise ErrorMensaje("Formato de error inválido")
    return datos["codigo"], datos["detalle"]
