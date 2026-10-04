"""Implementación del mecanismo de transferencia confiable de SACK.

Cada segmento enviado tiene un número de secuencia y se mantiene pendiente
hasta que es confirmado. Para cada segmento pendiente se registra además
el momento en que fue enviado.

Los ACK indican el número de secuencia del segmento que se quiere recibir
y los rangos indican qué segmentos siguientes a éste ya fueron recibidos
(fuera de orden).

La confirmación N indica que todos los segmentos con número de secuencia
menor que N fueron recibidos correctamente. Los segmentos recibidos fuera
de orden se almacenan temporalmente hasta poder entregarlos en el orden correcto.

Si un segmento permanece sin confirmar luego de vencer el timeout, este se
retransmite."""

import logging
import threading
import time

from ..canal import Canal
from lib.capas.udp.errores import ErrorTiempoEspera
from ..segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)

from ..sack_utiles import (
    codificar_ack_sack,
    decodificar_sack,
)

from lib.constantes import RTO_SACK

logger = logging.getLogger(__name__)


class CanalSack(Canal):
    def __init__(self, enlace):
        self._enlace = enlace
        self._proxima_secuencia = 0
        self._proxima_secuencia_recibir = 0
        self._recibidos = {}
        self._pendientes = {}
        self._tiempos_pendientes = {}
        self._rto = RTO_SACK

    def _calcular_rangos(self):
        """Agrupa en rangos los números de secuencia recibidos."""
        secuencias = sorted(self._recibidos)

        if not secuencias:
            return []

        rangos = []
        inicio = secuencias[0]
        fin = secuencias[0]

        for secuencia in secuencias[1:]:
            if secuencia == fin + 1:
                fin = secuencia
            else:
                rangos.append((inicio, fin))
                inicio = secuencia
                fin = secuencia

        rangos.append((inicio, fin))

        return rangos

    def _procesar_ack(self, segmento):
        """Actualiza los segmentos pendientes según el ACK recibido."""
        if segmento.tipo != TipoSegmento.ACK:
            return

        rangos = decodificar_sack(segmento.carga)

        logger.debug(
            "ACK recibido: confirmacion=%d, SACK=%s",
            segmento.confirmacion,
            rangos,
        )

        for secuencia in list(self._pendientes):
            if secuencia < segmento.confirmacion:
                del self._pendientes[secuencia]
                self._tiempos_pendientes.pop(secuencia, None)

        for inicio, fin in rangos:
            for secuencia in range(inicio, fin + 1):
                self._pendientes.pop(secuencia, None)
                self._tiempos_pendientes.pop(secuencia, None)

    def _recibir_ack(self):
        """Espera y procesa un segmento ACK."""
        try:
            while True:
                datos = self._enlace.recibir(self._rto)
                segmento = decodificar_segmento(datos)

                if segmento.tipo != TipoSegmento.ACK:
                    continue

                self._procesar_ack(segmento)
                return

        except ErrorTiempoEspera:
            return

    def _retransmitir_vencidos(self):
        """Retransmite los segmentos cuyo timeout se venció."""
        ahora = time.monotonic()

        for secuencia, tiempo in list(self._tiempos_pendientes.items()):
            if ahora - tiempo >= self._rto:
                segmento = self._pendientes[secuencia]

                logger.debug(
                    "Retransmitiendo segmento seq=%d por timeout",
                    secuencia,
                )

                self._enlace.enviar(codificar_segmento(segmento))
                self._tiempos_pendientes[secuencia] = ahora

    def enviar(self, datos: bytes):
        """Envía un segmento DATOS y lo mantiene pendiente de confirmación."""
        segmento = Segmento(
            tipo=TipoSegmento.DATOS,
            secuencia=self._proxima_secuencia,
            carga=datos,
        )

        logger.debug(
            "[%s] Enviando segmento DATOS seq=%d: %d bytes",
            threading.current_thread().name,
            self._proxima_secuencia,
            len(datos),
        )

        self._pendientes[self._proxima_secuencia] = segmento
        self._tiempos_pendientes[self._proxima_secuencia] = time.monotonic()

        self._enlace.enviar(codificar_segmento(segmento))
        self._proxima_secuencia += 1

    def recibir(self) -> bytes:
        """Recibe segmentos DATOS y los entrega en orden."""
        while True:
            if self._proxima_secuencia_recibir in self._recibidos:
                datos = self._recibidos.pop(
                    self._proxima_secuencia_recibir
                )
                self._proxima_secuencia_recibir += 1

                ack = codificar_ack_sack(
                    self._proxima_secuencia_recibir,
                    self._calcular_rangos(),
                )
                self._enlace.enviar(ack)

                return datos

            try:
                datos = self._enlace.recibir(self._rto)
            except ErrorTiempoEspera:
                self._retransmitir_vencidos()
                continue

            segmento = decodificar_segmento(datos)

            if segmento.tipo == TipoSegmento.ACK:
                self._procesar_ack(segmento)
                continue

            if segmento.tipo != TipoSegmento.DATOS:
                continue

            self._recibidos[segmento.secuencia] = segmento.carga

            if segmento.secuencia == self._proxima_secuencia_recibir:
                datos = self._recibidos.pop(
                    self._proxima_secuencia_recibir
                )
                self._proxima_secuencia_recibir += 1

                ack = codificar_ack_sack(
                    self._proxima_secuencia_recibir,
                    self._calcular_rangos(),
                )
                self._enlace.enviar(ack)

                return datos

            rangos = self._calcular_rangos()
            ack = codificar_ack_sack(
                self._proxima_secuencia_recibir,
                rangos,
            )
            self._enlace.enviar(ack)

    def vaciar(self):
        """Espera hasta que todos los segmentos pendientes sean confirmados."""
        while self._pendientes:
            self._retransmitir_vencidos()
            self._recibir_ack()

    def cerrar(self):
        """Limpia el estado pendiente del canal."""
        self._pendientes.clear()
        self._tiempos_pendientes.clear()
        self._recibidos.clear()