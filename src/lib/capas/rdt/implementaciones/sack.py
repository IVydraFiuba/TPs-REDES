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
from ..errores import ErrorSegmento
from lib.capas.udp.errores import ErrorComunicacion, ErrorTiempoEspera
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

from lib.constantes import (
    ACKS_DUPLICADOS_SACK,
    ALFA_SRTT,
    BETA_DEVRTT,
    K_DEVRTT,
    ESPERA_CIERRE,
    MAX_REINTENTOS_SACK,
    RTO_MAXIMO_SACK,
    RTO_MINIMO_SACK,
    RTO_SACK,
    VENTANA_SACK,
)

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
        self._sin_progreso = 0
        self._ultima_confirmacion = 0
        self._repetidos = 0
        self._srtt = None
        self._devrtt = 0.0
        self._retransmitidos = set()

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
            return RTO_SACK

        estimado = self._srtt + K_DEVRTT * self._devrtt
        return min(max(estimado, RTO_MINIMO_SACK), RTO_MAXIMO_SACK)

    def _confirmar(self):
        """Reenvia el ACK con el acumulativo y los bloques actuales."""
        self._enlace.enviar(codificar_ack_sack(
            self._proxima_secuencia_recibir,
            self._calcular_rangos(),
        ))

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

        confirmados = [secuencia for secuencia in self._pendientes
                       if secuencia < segmento.confirmacion]
        for inicio, fin in rangos:
            confirmados.extend(secuencia
                               for secuencia in range(inicio, fin + 1)
                               if secuencia in self._pendientes)

        limpio = None
        for secuencia in confirmados:
            if (secuencia not in self._retransmitidos
                    and (limpio is None or secuencia > limpio)):
                limpio = secuencia

        muestra = None
        if limpio is not None:
            muestra = self._tiempos_pendientes.get(limpio)

        for secuencia in confirmados:
            self._pendientes.pop(secuencia, None)
            self._tiempos_pendientes.pop(secuencia, None)
            self._retransmitidos.discard(secuencia)

        if muestra is not None:
            self._medir_rtt(time.monotonic() - muestra)
            self._rto = self._rto_estimado()

        if segmento.confirmacion > self._ultima_confirmacion:
            self._ultima_confirmacion = segmento.confirmacion
            self._repetidos = 0
            return

        if rangos:
            self._repetidos += 1
            if self._repetidos >= ACKS_DUPLICADOS_SACK:
                self._retransmitir(segmento.confirmacion)
                self._repetidos = 0

    def _retransmitir(self, secuencia):
        """Reenvia un segmento puntual y reinicia su temporizador."""
        segmento = self._pendientes.get(secuencia)
        if segmento is None:
            return

        logger.debug("Retransmision rapida del segmento seq=%d", secuencia)
        self._enlace.enviar(codificar_segmento(segmento))
        self._tiempos_pendientes[secuencia] = time.monotonic()
        self._retransmitidos.add(secuencia)

    def _recibir_ack(self):
        """Procesa un ACK. Devuelve False si vencio la espera.

        Distinguir los dos casos importa: un ACK que no libera nada
        significa que el par sigue vivo, y no debe agrandar el RTO.
        """
        try:
            while True:
                datos = self._enlace.recibir(self._rto)
                segmento = decodificar_segmento(datos)

                if segmento.tipo != TipoSegmento.ACK:
                    continue

                self._procesar_ack(segmento)
                return True

        except ErrorTiempoEspera:
            return False

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
                self._retransmitidos.add(secuencia)

    def _esperar_progreso(self):
        """Retransmite lo vencido y procesa un ACK, esperando avanzar.

        Si la ventana no se libera despues de MAX_REINTENTOS_SACK rondas,
        da al par por perdido en vez de reintentar para siempre.
        """
        antes = len(self._pendientes)

        self._retransmitir_vencidos()
        llego_ack = self._recibir_ack()

        if len(self._pendientes) < antes:
            self._sin_progreso = 0
            self._rto = self._rto_estimado()
            return

        if llego_ack:
            return

        self._sin_progreso += 1
        self._rto = min(self._rto * 2, RTO_MAXIMO_SACK)

        if self._sin_progreso > MAX_REINTENTOS_SACK:
            raise ErrorComunicacion(
                "El par dejo de confirmar: "
                f"{len(self._pendientes)} segmentos sin ACK"
            )

    def enviar(self, datos: bytes):
        """Envía un segmento DATOS y lo mantiene pendiente de confirmación.

        Bloquea mientras la ventana este llena, procesando los ACK que
        llegan. Asi los segmentos se confirman durante el envio y no se
        acumulan todos hasta el final.
        """
        while len(self._pendientes) >= VENTANA_SACK:
            self._esperar_progreso()

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

            if segmento.secuencia >= self._proxima_secuencia_recibir:
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
            self._esperar_progreso()

    def cerrar(self):
        """Responde duplicados un rato antes de soltar el canal.

        Nada protege el ACK del ultimo mensaje de la conversacion: si se
        pierde, el par lo retransmite. Cerrar en el acto lo deja hablando
        solo hasta que agota sus reintentos, que son decenas de segundos.
        Es el mismo motivo por el que TCP tiene TIME_WAIT.
        """
        limite = time.monotonic() + max(4 * self._rto, ESPERA_CIERRE)
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
                self._confirmar()

        self._pendientes.clear()
        self._tiempos_pendientes.clear()
        self._recibidos.clear()
        self._retransmitidos.clear()
        self._sin_progreso = 0
        self._rto = RTO_SACK