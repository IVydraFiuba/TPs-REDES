# lib/stopwait.py
class StopWaitTransport:
    """Transferencia confiable con Stop & Wait.

    Contrato (igual que SackTransport, para que cliente/servidor
    las usen indistintamente):
      - send(data): manda todos los bytes de forma confiable.
      - recv():     devuelve el proximo bloque; b'' = EOF.
      - close():    cierra ordenadamente y libera el socket.
    """

    # TODO(Parte 2): implementar Stop & Wait.
    #   - send: numero de secuencia, esperar ACK, timeout + retransmision
    #   - recv: validar seq, mandar ACK, entregar en orden; b'' en FIN
    #   - close: enviar FIN y liberar el socket
    #   Wire format de segmentos: interno tuyo. Tolerar 10% perdida, RTT 300ms.

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
