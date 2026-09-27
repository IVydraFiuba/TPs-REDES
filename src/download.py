import logging

from lib.args import parsear_argumentos_descarga
from lib.logger import configurar_logger

logger = logging.getLogger(__name__)

# TODO(Persona 5): cliente de download.
# Ejemplo: python src/download.py -H 127.0.0.1 -p 8080
#          -d ./foto.jpg -n foto.jpg -r sw


if __name__ == "__main__":
    args = parsear_argumentos_descarga()
    configurar_logger(args.verbose, args.quiet)
    logger.info(f"Verbose: {args.verbose}")
    logger.info(f"Quiet: {args.quiet}")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"FILEPATH: {args.dst}")
    logger.info(f"FILENAME: {args.name}")
    logger.info(f"Protocol: {args.protocol}")
    # TODO: descarga real.
    #   1. protocol.conectar((args.host, args.port), OP_DOWNLOAD,
    #      PROTOCOLS[args.protocol], args.name, 0) devuelve
    #      (sock, data_addr, filesize): en DOWNLOAD el filesize lo pone
    #      el servidor en la respuesta, por eso se manda 0. Envolver en
    #      try/except ConnectionError: ahi cae el archivo inexistente
    #      (ERR_FILE_NOT_FOUND) y el servidor que no responde.
    #   2. crear_transport(PROTOCOLS[args.protocol], sock, data_addr)
    #   3. abrir args.dst y escribir lo que devuelva transport.recv()
    #      hasta que devuelva b'' (EOF). Abrir el archivo recien
    #      despues del handshake, para no crear un archivo vacio
    #      cuando el pedido se rechaza.
    #   4. comparar los bytes escritos contra el filesize del
    #      handshake: si son menos, la transferencia quedo incompleta
    #      (recv() corto por MAX_RETRIES timeouts). Avisar con
    #      logger.error y salir con codigo != 0; el archivo parcial
    #      queda en disco, no lo borramos.
    #   5. transport.close() y sock.close(), tambien si algo falla en
    #      el medio (try/finally).
