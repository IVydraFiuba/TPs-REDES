"""Establecimiento de una sesión RDT sobre un enlace UDP."""

import logging

from lib.constantes import (
    MAX_REINTENTOS_SYN,
    RTO_MAXIMO_SYN,
    RTO_SYN,
)

from ..udp.errores import ErrorComunicacion, ErrorTiempoEspera
from .errores import ErrorSegmento
from .segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)

logger = logging.getLogger(__name__)


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
    """Pide una sesion y espera el eco del servidor.

    Reintenta porque el SYN se puede perder como cualquier datagrama.
    Repetirlo no abre una segunda sesion: el despachador reconoce un SYN
    de una direccion que ya tiene sesion viva y reenvia la misma
    respuesta.
    """
    syn = codificar_syn(protocolo)
    rto = RTO_SYN

    for intento in range(MAX_REINTENTOS_SYN):
        enlace.enviar(syn)
        try:
            respuesta = decodificar_segmento(enlace.recibir(timeout=rto))
        except (ErrorTiempoEspera, ErrorSegmento):
            logger.debug("SYN sin respuesta, reintento %d", intento + 1)
            rto = min(rto * 2, RTO_MAXIMO_SYN)
            continue

        if (respuesta.tipo == TipoSegmento.SYN
                and respuesta.carga == bytes([protocolo])):
            return

        logger.debug("Respuesta de establecimiento inesperada: %s",
                     respuesta.tipo.name)

    raise ErrorComunicacion(
        "El servidor no respondio al establecimiento de sesion"
    )
