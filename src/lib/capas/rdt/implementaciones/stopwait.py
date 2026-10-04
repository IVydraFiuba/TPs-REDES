"""Transferencia confiable con Stop & Wait.

Un segmento en vuelo por vez: se envía y no se continúa hasta que llega
su confirmación. Lo único que provoca una retransmisión es el
vencimiento del timeout; el RTO se duplica en cada intento.

El RTO no es fijo: se estima a partir del RTT que se mide en cada
confirmación, igual que TCP. Un valor fijo o bien es demasiado corto y
retransmite de más, o bien es demasiado largo y se pasa esperando.

El campo `confirmacion` lleva el próximo número de secuencia esperado,
igual que en SACK, de modo que el significado del campo no depende del
protocolo que se haya negociado.
"""

import logging
import threading
import time
from queue import Queue

from lib.constantes import (
    ALFA_SRTT,
    ESPERA_CIERRE,
    BETA_DEVRTT,
    K_DEVRTT,
    MAX_REINTENTOS_SW,
    RTO_MAXIMO_SW,
    RTO_MINIMO_SW,
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
        self._srtt = None
        self._devrtt = 0.0

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

    def _medir_rtt(self, muestra):
        """Incorpora una muestra de RTT al estimador."""
        if self._srtt is None:
            self._srtt = muestra
            self._devrtt = muestra / 2
            return

        self._devrtt = ((1 - BETA_DEVRTT) * self._devrtt
                        + BETA_DEVRTT * abs(muestra - self._srtt))
        self._srtt = (1 - ALFA_SRTT) * self._srtt + ALFA_SRTT * muestra

    def _rto_estimado(self):
        """RTO a partir del RTT medido, acotado entre el piso y el techo."""
        if self._srtt is None:
            return RTO_SW

        estimado = self._srtt + K_DEVRTT * self._devrtt
        return min(max(estimado, RTO_MINIMO_SW), RTO_MAXIMO_SW)

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
        enviado_en = time.monotonic()
        self._enlace.enviar(segmento)

        intentos = 0
        retransmitido = False
        while True:
            try:
                recepcion = decodificar_segmento(
                    self._enlace.recibir(timeout=self._rto)
                )
            except ErrorTiempoEspera:
                intentos = self._retransmitir(segmento, intentos)
                retransmitido = True
                continue
            except ErrorSegmento:
                continue

            if recepcion.tipo == TipoSegmento.ACK:
                if recepcion.confirmacion > self.secuencia_actual_envio:
                    self.secuencia_actual_envio += 1
                    #Los retrasmitidos no sirven como muestra
                    if not retransmitido:
                        self._medir_rtt(time.monotonic() - enviado_en)
                        self._rto = self._rto_estimado()
                    logger.debug("SW: ACK correcto, rto=%.3f", self._rto)
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

    def _espera_cierre(self):
        """Cuanto responder rezagados antes de soltar el canal.

        Escala con el RTT medido, no con el RTO. Un receptor que midio
        una sola vez tiene el mismo SRTT que uno que midio mil; lo que
        los diferencia es DEVRTT, que aca no viene al caso. Queda el
        default solo si nada de lo que este canal envio fue confirmado
        nunca.
        """
        base = self._srtt if self._srtt is not None else RTO_SW
        return max(4 * base, ESPERA_CIERRE)

    def cerrar(self):
        """Responde duplicados un rato antes de soltar el canal.

        Nada protege el ACK del ultimo mensaje de la conversacion: si se
        pierde, el par lo retransmite. Cerrar en el acto lo deja hablando
        solo hasta que agota sus reintentos, que son decenas de segundos.
        Es el mismo motivo por el que TCP tiene TIME_WAIT.

        Lo que hay que cubrir son un par de round trips, asi que la
        espera sale del RTT y no del RTO. Escalar con `self._rto` lo
        hace crecer con el backoff: si el par acaba de darse por
        muerto, el RTO quedo en el techo y serian 32 segundos de
        espera. Y el RTO estimado tampoco sirve, porque lleva
        4*DEVRTT de margen para no retransmitir de mas, margen que
        aca no significa nada.
        """
        limite = time.monotonic() + self._espera_cierre()
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                break
            try:
                segmento = decodificar_segmento(
                    self._enlace.recibir(timeout=restante)
                )
            except ErrorSegmento:
                continue
            except (ErrorTiempoEspera, ErrorComunicacion):
                break

            if segmento.tipo == TipoSegmento.DATOS:
                self._procesar_datos(segmento)
