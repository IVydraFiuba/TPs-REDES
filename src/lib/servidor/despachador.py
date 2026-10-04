"""Recibe datagramas UDP y los distribuye a una sesión por endpoint."""

import logging
import socket
import threading

from lib.capas.rdt.errores import ErrorModoNoImplementado, ErrorSegmento
from lib.capas.rdt.establecimiento import codificar_syn, leer_solicitud_sesion
from lib.capas.rdt.fabrica import crear_canal, validar_modo
from lib.capas.rdt.segmento import TipoSegmento, decodificar_segmento
from lib.capas.udp import EnlaceSesionUdp
from lib.capas.udp.errores import ErrorComunicacion
from lib.constantes import (
    CAPACIDAD_COLA_SESION,
    MAXIMO_SESIONES,
    TAMANIO_MAX_DATAGRAMA,
    TIMEOUT_DESPACHADOR,
)

from .registro_sesiones import EntradaSesion, RegistroSesiones
from .sesion import SesionServidor

logger = logging.getLogger(__name__)


class Despachador:
    def __init__(self, conexion, almacenamiento, detener,
                 maximo_sesiones=MAXIMO_SESIONES):
        self._conexion = conexion
        self._almacenamiento = almacenamiento
        self._detener = detener
        self._registro = RegistroSesiones(maximo_sesiones)

    def ejecutar(self):
        self._conexion.settimeout(TIMEOUT_DESPACHADOR)
        try:
            while not self._detener.is_set():
                try:
                    datos, direccion = self._conexion.recvfrom(
                        TAMANIO_MAX_DATAGRAMA + 1
                    )
                except socket.timeout:
                    continue
                self._distribuir(datos, direccion)
        finally:
            for hilo in self._registro.interrumpir_todas():
                hilo.join(timeout=2)

    def _distribuir(self, datos, direccion):
        try:
            segmento = decodificar_segmento(datos)
            logger.debug(
                "[%s] Datagrama recibido de %s: tipo=%s, %d bytes",
                threading.current_thread().name,
                direccion,
                segmento.tipo.name,
                len(datos)
            )
            if segmento.tipo == TipoSegmento.SYN:
                self._establecer(direccion, segmento)
                return

            entrada = self._registro.buscar(direccion)
            if entrada is None:
                self._contestar_rezagado(direccion, segmento)
            elif not entrada.enlace.entregar(datos):
                logger.debug(
                    "[%s] Cola llena o sesion cerrada: %s",
                    threading.current_thread().name,
                    direccion
                )
        except (ErrorSegmento, ErrorModoNoImplementado,
                ErrorComunicacion, OSError, RuntimeError) as error:
            logger.warning(
                "[%s] Datagrama de %s descartado: %s",
                threading.current_thread().name,
                direccion,
                error
            )

    def _contestar_rezagado(self, direccion, segmento):
        """Reenvia el ultimo ACK de una sesion que acaba de cerrar.

        El ACK del ultimo mensaje de una transferencia no esta protegido
        por nada: si se pierde, el par lo retransmite. Reenviar el ACK
        que la sesion mando al final lo desbloquea en un RTO, en vez de
        dejarlo retransmitir hasta agotar sus reintentos.
        """
        respuesta = None
        if segmento.tipo == TipoSegmento.DATOS:
            respuesta = self._registro.respuesta_en_espera(direccion)

        if respuesta is None:
            logger.debug(
                "[%s] Sesion desconocida para %s",
                threading.current_thread().name,
                direccion
            )
            return

        logger.debug(
            "[%s] Rezagado de %s: reenvio el ultimo ACK",
            threading.current_thread().name,
            direccion
        )
        self._conexion.sendto(respuesta, direccion)

    def _establecer(self, direccion, segmento):
        protocolo = leer_solicitud_sesion(segmento)
        entrada = self._registro.buscar(direccion)
        if entrada is not None:
            if protocolo == entrada.protocolo:
                entrada.enlace.enviar(entrada.respuesta_syn)
            return

        validar_modo(protocolo)

        enlace = EnlaceSesionUdp(
            self._conexion,
            direccion,
            capacidad=CAPACIDAD_COLA_SESION,
        )
        respuesta = codificar_syn(protocolo)
        entrada = EntradaSesion(protocolo, enlace, respuesta)
        if not self._registro.agregar(direccion, entrada):
            logger.warning(
                "Límite de sesiones alcanzado; se rechaza %s", direccion
            )
            return

        try:
            canal = crear_canal(protocolo, enlace)
            sesion = SesionServidor(canal, self._almacenamiento)
            entrada.hilo = threading.Thread(
                target=self._ejecutar_sesion,
                args=(direccion, entrada, sesion),
                daemon=True,
                name=f"sesion-{direccion[0]}:{direccion[1]}",
            )
            enlace.enviar(respuesta)
            entrada.hilo.start()
            logger.info(
                "[%s] Sesion iniciada para %s (protocolo=%d)",
                threading.current_thread().name,
                direccion,
                protocolo
            )
        except Exception:
            self._registro.quitar(direccion)
            enlace.interrumpir()
            raise

    def _ejecutar_sesion(self, direccion, entrada, sesion):
        try:
            sesion.ejecutar()
        finally:
            self._registro.quitar(direccion)
            entrada.enlace.interrumpir()
