"""Recibe datagramas UDP y los distribuye a una sesión por endpoint."""

import logging
import socket
import threading

from lib.constantes import (
    CAPACIDAD_COLA_DIRECTO,
    MAXIMO_SESIONES,
    PROTO_DIRECTO,
    TAMANIO_MAX_DATAGRAMA,
    TIMEOUT_SERVIDOR,
)
from lib.rdt.errores import ErrorModoNoImplementado, ErrorSegmento
from lib.rdt.establecimiento import codificar_syn, leer_solicitud_sesion
from lib.rdt.fabrica import crear_canal
from lib.rdt.segmento import TipoSegmento, decodificar_segmento
from lib.udp import EnlaceSesionUdp
from lib.udp.errores import ErrorComunicacion

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
        self._conexion.settimeout(TIMEOUT_SERVIDOR)
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
            if segmento.tipo == TipoSegmento.SYN:
                self._establecer(direccion, segmento)
                return

            entrada = self._registro.buscar(direccion)
            if entrada is None:
                logger.debug(
                    "Datagrama de sesión desconocida: %s", direccion
                )
            elif not entrada.enlace.entregar(datos):
                logger.debug(
                    "Cola llena o sesión cerrada: %s", direccion
                )
        except (ErrorSegmento, ErrorModoNoImplementado,
                ErrorComunicacion, OSError, RuntimeError) as error:
            logger.warning(
                "Datagrama de %s descartado: %s", direccion, error
            )

    def _establecer(self, direccion, segmento):
        protocolo = leer_solicitud_sesion(segmento)
        entrada = self._registro.buscar(direccion)
        if entrada is not None:
            if protocolo == entrada.protocolo:
                entrada.enlace.enviar(entrada.respuesta_syn)
            return

        if protocolo != PROTO_DIRECTO:
            raise ErrorModoNoImplementado(
                f"Protocolo {protocolo} aún no implementado"
            )

        enlace = EnlaceSesionUdp(
            self._conexion,
            direccion,
            capacidad=CAPACIDAD_COLA_DIRECTO,
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
