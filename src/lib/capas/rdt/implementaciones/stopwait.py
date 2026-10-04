"""Transferencia confiable con Stop & Wait.

Un segmento en vuelo por vez: se envía y no se continúa hasta que llega
su confirmación. Lo único que provoca una retransmisión es el
vencimiento del timeout; el RTO se duplica en cada intento y vuelve a su
valor inicial con cada confirmación que avanza.

El campo `confirmacion` lleva el próximo número de secuencia esperado,
igual que en SACK, de modo que el significado del campo no depende del
protocolo que se haya negociado.
"""

import logging
import threading
from queue import Queue

from lib.constantes import (
    MAX_REINTENTOS_SW,
    RTO_MAXIMO_SW,
    RTO_SW,
)

from ...udp.errores import ErrorComunicacion, ErrorTiempoEspera
from ..canal import Canal
from ..errores import ErrorSegmento
from ..segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)

logger = logging.getLogger(__name__)


class CanalStopWait(Canal):
    def __init__(self, enlace):
        self._enlace = enlace
        self.secuencia_actual_envio = 0
        self.secuencia_actual_recepcion = 0
        self.datos_en_espera = Queue()
        self._rto = RTO_SW

    # ------------------------------------------------------- recepción

    def _confirmar(self):
        """Confirma el próximo segmento que se espera recibir."""
        self._enlace.enviar(codificar_segmento(Segmento(
            TipoSegmento.ACK,
            confirmacion=self.secuencia_actual_recepcion,
        )))

    def _procesar_datos(self, segmento):
        """Devuelve la carga si el segmento llegó en orden, o None.

        Un segmento fuera de orden o repetido se descarta, pero se
        vuelve a confirmar igual: si no, el emisor lo retransmite para
        siempre porque cree que su ACK anterior se perdió.
        """
        if segmento.secuencia != self.secuencia_actual_recepcion:
            logger.debug("SW: DATOS seq=%d fuera de orden, esperaba %d",
                         segmento.secuencia,
                         self.secuencia_actual_recepcion)
            self._confirmar()
            return None

        self.secuencia_actual_recepcion += 1
        self._confirmar()
        return segmento.carga

    # --------------------------------------------------------- emisión

    def _retransmitir(self, segmento, intentos):
        """Reenvía el segmento en vuelo y agranda el RTO."""
        intentos += 1
        if intentos > MAX_REINTENTOS_SW:
            raise ErrorComunicacion(
                "El par no confirmó el segmento "
                f"{self.secuencia_actual_envio}"
            )

        self._rto = min(self._rto * 2, RTO_MAXIMO_SW)
        logger.debug("SW: timeout, retransmito seq=%d (intento %d)",
                     self.secuencia_actual_envio, intentos)
        self._enlace.enviar(segmento)
        return intentos

    def enviar(self, datos: bytes):
        """Envía un segmento y no vuelve hasta que lo confirmen."""
        logger.debug("[%s] SW: enviando DATOS seq=%d, %d bytes",
                     threading.current_thread().name,
                     self.secuencia_actual_envio, len(datos))

        segmento = codificar_segmento(Segmento(
            TipoSegmento.DATOS,
            secuencia=self.secuencia_actual_envio,
            carga=datos,
        ))
        self._enlace.enviar(segmento)

        intentos = 0
        while True:
            try:
                recepcion = decodificar_segmento(
                    self._enlace.recibir(timeout=self._rto)
                )
            except ErrorTiempoEspera:
                intentos = self._retransmitir(segmento, intentos)
                continue
            except ErrorSegmento:
                continue

            if recepcion.tipo == TipoSegmento.ACK:
                if recepcion.confirmacion > self.secuencia_actual_envio:
                    self.secuencia_actual_envio += 1
                    self._rto = RTO_SW
                    logger.debug("SW: ACK correcto")
                    return
                continue

            if recepcion.tipo == TipoSegmento.DATOS:
                carga = self._procesar_datos(recepcion)
                if carga is not None:
                    self.datos_en_espera.put(carga)

    def recibir(self) -> bytes:
        """Devuelve el próximo bloque en orden."""
        if not self.datos_en_espera.empty():
            return self.datos_en_espera.get()

        intentos = 0
        while True:
            try:
                segmento = decodificar_segmento(
                    self._enlace.recibir(timeout=RTO_MAXIMO_SW)
                )
            except ErrorTiempoEspera:
                intentos += 1
                if intentos > MAX_REINTENTOS_SW:
                    raise ErrorComunicacion("El par dejó de enviar datos")
                continue
            except ErrorSegmento:
                continue

            intentos = 0

            if segmento.tipo != TipoSegmento.DATOS:
                continue

            carga = self._procesar_datos(segmento)
            if carga is not None:
                return carga

    def vaciar(self):
        """No hace nada: `enviar` ya vuelve con el segmento confirmado."""

    def cerrar(self):
        pass
