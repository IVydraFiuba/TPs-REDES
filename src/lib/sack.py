# lib/sack.py
class SackTransport:
    """Transferencia confiable con SACK (estilo TCP).

    Mismo contrato que StopWaitTransport:
      - send(data): manda todos los bytes de forma confiable.
      - recv():     devuelve el proximo bloque; b'' = EOF.
      - close():    cierra ordenadamente y libera el socket.
    """

    # TODO(Parte 3): implementar SACK (estilo TCP).
    #   - ventana deslizante, buffers, bloques SACK, retransmision selectiva
    #   Objetivo: 5 MB en <2 min con 10% perdida y RTT 40ms.

    def __init__(self, sock, peer_addr, logger):
        self._sock = sock
        self._peer = peer_addr
        self._log = logger

    def send(self, data):
        raise NotImplementedError

    def recv(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
