import logging

from lib.args import parsear_argumentos_subida
from lib.logger import configurar_logger

logger = logging.getLogger(__name__)


def print_debug_args(args):
    logger.info(f"Verbose: {args.verbose}")
    logger.info(f"Quiet: {args.quiet}")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"FILEPATH: {args.src}")
    logger.info(f"FILENAME: {args.name}")
    logger.info(f"Protocol: {args.protocol}")

def main_subida():
    args = parsear_argumentos_subida()
    configurar_logger(args.verbose, args.quiet)
    print_debug_args(args)

if __name__ == "__main__":
    main_subida()