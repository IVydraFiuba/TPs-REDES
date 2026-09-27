# lib/sack.py
import logging

logger = logging.getLogger(__name__)


class SackTransport:
    """Transferencia confiable con SACK (estilo TCP).

    Mismo contrato que StopWaitTransport:
      - send(data): manda todos los bytes de forma confiable.
      - recv():     devuelve el proximo bloque; b'' = EOF.
      - close():    cierra ordenadamente y libera el socket.

    El formato de los segmentos esta en lib/segmento.py y es el mismo
    que usa StopWaitTransport.
    """

    def __init__(self, sock, peer_addr):
        self._sock = sock
        self._peer = peer_addr

    def send(self, data):
        raise NotImplementedError

    def recv(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
