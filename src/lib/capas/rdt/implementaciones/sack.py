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
    ESPERA_RECEPCION_SACK,
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

    def _guardar(self, segmento):
        """Almacena un DATOS, salvo que sea un duplicado ya entregado.

        No avanza `_proxima_secuencia_recibir`: eso es tarea exclusiva
        de `_entregar`, que es quien devuelve el dato a la aplicacion.
        """
        if segmento.secuencia >= self._proxima_secuencia_recibir:
            self._recibidos[segmento.secuencia] = segmento.carga

    def _entregar(self):
        """Saca el proximo segmento en orden, avanza y confirma."""
        datos = self._recibidos.pop(self._proxima_secuencia_recibir)
        self._proxima_secuencia_recibir += 1
        self._confirmar()
        return datos

    def _recibir_datos(self, segmento):
        """Guarda un DATOS entrante y lo confirma.

        Un duplicado ya entregado no se guarda, pero se confirma igual:
        el par lo esta retransmitiendo justamente porque cree que no
        llego.
        """
        self._guardar(segmento)
        self._confirmar()

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
                if segmento.confirmacion not in self._retransmitidos:
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
        """Procesa lo que llegue del par. Devuelve False si vencio la espera.

        Distinguir los dos casos importa: algo que llega y no libera
        nada significa que el par sigue vivo, y no debe agrandar el RTO.

        Un DATOS que aparece mientras esperamos un ACK no se descarta:
        se guarda y se confirma. Descartarlo deja al par retransmitiendo
        hasta agotar sus reintentos, porque cree que su segmento nunca
        llego, y con el RTO en el techo eso son decenas de segundos. Es
        lo que pasaba con el ACEPTADO del servidor durante una subida:
        el cliente, con la ventana sin llenarse, nunca pasaba por
        `recibir`, que es el otro lugar donde se confirman los DATOS.
        """
        try:
            while True:
                datos = self._enlace.recibir(self._rto)
                segmento = decodificar_segmento(datos)

                if segmento.tipo == TipoSegmento.DATOS:
                    self._recibir_datos(segmento)
                    return True

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

    def _retransmitir_mas_viejo(self):
        """Reenvia el pendiente mas antiguo sin mirar su temporizador."""
        if self._pendientes:
            self._retransmitir(min(self._pendientes))

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

        # Vencio la espera sin novedades. El reenvio va ANTES de agrandar
        # el RTO: si se agranda primero, `_retransmitir_vencidos` compara
        # el tiempo transcurrido contra un RTO que crece mas rapido que
        # el reloj (1, 2, 4, 8...) y el segmento no sale hasta la cuarta
        # ronda, a los 15 segundos de haberse enviado.
        self._retransmitir_mas_viejo()

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
        """Recibe segmentos DATOS y los entrega en orden.

        Corta con ErrorComunicacion si el par deja de hablar por mas de
        ESPERA_RECEPCION_SACK. Sin ese tope, un cliente que muere a
        mitad de una transferencia deja el hilo de la sesion girando
        para siempre: nunca corre el `finally` que la saca del registro,
        y el servidor termina rechazando sesiones nuevas por el limite
        de MAXIMO_SESIONES.

        El tope es por tiempo y no por cantidad de intentos, porque cada
        intento espera `self._rto`, que puede estar en el piso de 50 ms.
        Diez intentos serian medio segundo de paciencia y cortaria
        transferencias sanas.
        """
        limite = time.monotonic() + ESPERA_RECEPCION_SACK
        while True:
            if self._proxima_secuencia_recibir in self._recibidos:
                return self._entregar()

            try:
                datos = self._enlace.recibir(self._rto)
            except ErrorTiempoEspera:
                self._retransmitir_vencidos()
                if time.monotonic() >= limite:
                    raise ErrorComunicacion(
                        "El par dejo de enviar datos"
                    )
                continue

            limite = time.monotonic() + ESPERA_RECEPCION_SACK
            segmento = decodificar_segmento(datos)

            if segmento.tipo == TipoSegmento.ACK:
                self._procesar_ack(segmento)
                continue

            if segmento.tipo != TipoSegmento.DATOS:
                continue

            self._guardar(segmento)

            if self._proxima_secuencia_recibir in self._recibidos:
                return self._entregar()

            self._confirmar()

    def vaciar(self):
        """Espera hasta que todos los segmentos pendientes sean confirmados."""
        while self._pendientes:
            self._esperar_progreso()

    def _espera_cierre(self):
        """Cuanto responder rezagados antes de soltar el canal.

        Escala con el RTT medido, no con el RTO. Un receptor que midio
        una sola vez tiene el mismo SRTT que uno que midio mil; lo que
        los diferencia es DEVRTT, que aca no viene al caso. Queda el
        default solo si nada de lo que este canal envio fue confirmado
        nunca.
        """
        base = self._srtt if self._srtt is not None else RTO_SACK
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
                self._confirmar()

        self._pendientes.clear()
        self._tiempos_pendientes.clear()
        self._recibidos.clear()
        self._retransmitidos.clear()
        self._sin_progreso = 0
        self._rto = RTO_SACK