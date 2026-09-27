import logging

from lib.args import parsear_argumentos_servidor
from lib.logger import configurar_logger

logger = logging.getLogger(__name__)

# TODO(Parte 4): servidor real.
#   - escuchar; usar protocol.recibir_handshake / responder_handshake
#   - chequear archivo/espacio (condiciones de error), guardar en storage
#   - obtener canal con crear_transport; un thread por cliente (concurrencia)
#  Ejemplo: python src/start-server.py -H 127.0.0.1 -p 8080 -s ./storage


if __name__ == "__main__":
    args = parsear_argumentos_servidor()
    configurar_logger(args.verbose, args.quiet)
    logger.info(f"Verbose: {args.verbose}")
    logger.info(f"Quiet: {args.quiet}")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Storage: {args.storage}")
