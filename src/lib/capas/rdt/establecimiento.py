"""Establecimiento de una sesión RDT sobre un enlace UDP."""

from .errores import ErrorSegmento
from .segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)


def codificar_syn(protocolo):
    if type(protocolo) is not int or not 0 <= protocolo <= 0xff:
        raise ErrorSegmento("Protocolo inválido")
    return codificar_segmento(
        Segmento(TipoSegmento.SYN, carga=bytes([protocolo]))
    )


def leer_solicitud_sesion(segmento):
    if segmento.tipo != TipoSegmento.SYN or len(segmento.carga) != 1:
        raise ErrorSegmento("Solicitud de sesión inválida")
    return segmento.carga[0]


def solicitar_sesion(enlace, protocolo):
    enlace.enviar(codificar_syn(protocolo))
    respuesta = decodificar_segmento(enlace.recibir())
    if (respuesta.tipo != TipoSegmento.SYN
            or respuesta.carga != bytes([protocolo])):
        raise ErrorSegmento("Respuesta de establecimiento inesperada")
