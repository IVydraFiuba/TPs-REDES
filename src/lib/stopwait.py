# lib/stopwait.py
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

    # TODO(Parte 2): implementar Stop & Wait.
    #   Arranca con: from lib import segmento
    #   Tolerar 10% de perdida y RTT de hasta 300 ms.

    def __init__(self, sock, peer_addr, logger):
        self._sock = sock
        self._peer = peer_addr
        self._log = logger

    def send(self, data):
        # TODO: partir data en trozos de PAYLOAD_SIZE y, por cada uno:
        #   1. mandar segmento.empaquetar_data(seq, trozo) al peer
        #   2. esperar el ACK con timeout y leerlo con
        #      segmento.desempaquetar(datos)
        #   3. si el .seq del ACK es mayor que seq, el trozo llego:
        #      seguir con el siguiente
        #      si vence el timeout: retransmitir el mismo trozo
        raise NotImplementedError

    def recv(self):
        # TODO: recibir del socket y segmento.desempaquetar(datos).
        #   - DATA con .seq == el esperado: responder
        #     segmento.empaquetar_ack(esperado + 1) y devolver .payload
        #   - DATA con .seq menor: es un duplicado, volver a mandar el
        #     ACK y descartar el payload (si no, el emisor se cuelga)
        #   - FIN: devolver b'' (el emisor no espera respuesta)
        #   - recv() tiene que tener timeout: si el FIN se pierde,
        #     sin timeout el receptor espera para siempre. Despues de
        #     MAX_RETRIES timeouts seguidos sin recibir nada, dar la
        #     conexion por cerrada y devolver b''. El que llama compara
        #     lo escrito contra el filesize del handshake para saber si
        #     quedo incompleto.
        raise NotImplementedError

    def close(self):
        # TODO: emisor -> mandar segmento.empaquetar_fin() unas cuantas
        #   veces espaciadas y cerrar, sin esperar confirmacion.
        #   receptor -> antes de cerrar, quedarse un rato respondiendo
        #   los DATA y FIN duplicados que sigan llegando. Si cierra de
        #   una y se perdio el ultimo ACK, el emisor queda retransmitiendo
        #   contra un socket cerrado.
        raise NotImplementedError
