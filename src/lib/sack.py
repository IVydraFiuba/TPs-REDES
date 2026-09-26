# lib/sack.py
class SackTransport:
    """Transferencia confiable con SACK (estilo TCP).

    Mismo contrato que StopWaitTransport:
      - send(data): manda todos los bytes de forma confiable.
      - recv():     devuelve el proximo bloque; b'' = EOF.
      - close():    cierra ordenadamente y libera el socket.

    El formato de los segmentos esta en lib/segmento.py y es el mismo
    que usa StopWaitTransport.
    """

    # TODO(Parte 3): implementar SACK (estilo TCP).
    #   Arranca con: from lib import segmento
    #   Objetivo: 5 MB en menos de 2 min con 10% de perdida y RTT 40ms.

    def __init__(self, sock, peer_addr, logger):
        self._sock = sock
        self._peer = peer_addr
        self._log = logger

    def send(self, data):
        # TODO: partir data en trozos de PAYLOAD_SIZE y mantener hasta
        #   WINDOW_SIZE trozos en vuelo:
        #   - mandar segmento.empaquetar_data(seq, trozo) de todos los
        #     que entren en la ventana, sin esperar ACK
        #   - leer los ACK con segmento.desempaquetar(datos): .seq es
        #     el primero que falta y .bloques son los tramos que el
        #     receptor ya tiene (los dos extremos incluidos)
        #   - lo que no cubre ni .seq ni ningun bloque es lo que falta:
        #     retransmitir solo eso
        #   - 3 ACK seguidos marcando el mismo agujero: retransmitir ya,
        #     sin esperar el timeout
        raise NotImplementedError

    def recv(self):
        # TODO: recibir y leer con segmento.desempaquetar(datos).
        #   - guardar en un buffer los DATA que lleguen fuera de orden
        #   - responder segmento.empaquetar_ack(proximo, bloques),
        #     donde proximo es el primero que falta y bloques son los
        #     tramos del buffer que estan por encima de proximo
        #     (como mucho MAX_BLOQUES_SACK)
        #   - devolver los payloads en orden; b'' al recibir el FIN
        raise NotImplementedError

    def close(self):
        # TODO: si fui el emisor, mandar segmento.empaquetar_fin() y
        #   esperar el FINACK, retransmitiendo el FIN hasta MAX_RETRIES.
        #   Despues cerrar el socket.
        raise NotImplementedError
