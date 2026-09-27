import logging

from lib.args import parsear_argumentos_subida
from lib.logger import configurar_logger

logger = logging.getLogger(__name__)

# TODO(Persona 5): cliente de upload.
#  Ejemplo: python src/upload.py -H 127.0.0.1 -p 8080
#           -s ./foto.jpg -n foto.jpg -r sw


if __name__ == "__main__":
    args = parsear_argumentos_subida()
    configurar_logger(args.verbose, args.quiet)
    logger.info(f"Verbose: {args.verbose}")
    logger.info(f"Quiet: {args.quiet}")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"FILEPATH: {args.src}")
    logger.info(f"FILENAME: {args.name}")
    logger.info(f"Protocol: {args.protocol}")
    # TODO: subida real.
    #   1. abrir args.src y sacar el filesize con os.path.getsize:
    #      va en el handshake para que el servidor sepa cuanto espera
    #      y pueda rechazar por falta de espacio (ERR_NO_SPACE). Si el
    #      archivo no existe o no se puede leer, logger.error y salir
    #      con codigo != 0 sin tocar la red.
    #   2. protocol.conectar((args.host, args.port), OP_UPLOAD,
    #      PROTOCOLS[args.protocol], args.name, filesize)
    #      devuelve (sock, data_addr, _): data_addr es el puerto propio
    #      de la sesion, no el de escucha. Envolver en try/except
    #      ConnectionError: ahi caen el rechazo del servidor y el
    #      servidor que no responde.
    #   3. crear_transport(PROTOCOLS[args.protocol], sock, data_addr)
    #   4. leer el archivo por trozos y transport.send(trozo) hasta EOF
    #   5. transport.close() y sock.close(), tambien si algo falla en el
    #      medio (try/finally): si no, queda el socket abierto y el
    #      servidor esperando el FIN.
