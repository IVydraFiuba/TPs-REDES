# lib/stopwait.py
import logging

logger = logging.getLogger(__name__)


class StopWaitTransport:
    """Transferencia confiable con Stop & Wait.

    Contrato (igual que SackTransport, para que cliente/servidor
    las usen indistintamente):
      - send(data): manda todos los bytes de forma confiable.
      - recv():     devuelve el proximo bloque; b'' = EOF.
      - close():    cierra ordenadamente y libera el socket.

    El formato de los segmentos esta en lib/segmento.py y es el mismo
    que usa SackTransport. Stop & Wait no manda bloques SACK: sus ACK
    van sin bloques.
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
