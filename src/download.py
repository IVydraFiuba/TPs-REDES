import logging

from lib.args import parsear_argumentos_descarga
from lib.logger import configurar_logger

logger = logging.getLogger(__name__)

# TODO(Persona 5): cliente real.
#   - protocol.conectar(...) con -r mapeado por PROTOCOLS; luego send/recv
#   - (aparte) topologia mininet, capturas y analisis SACK vs S&W
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
