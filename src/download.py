import logging

from lib.args import parsear_argumentos_descarga
from lib.cliente.mock_cliente import Cliente
from lib.logger import configurar_logger

logger = logging.getLogger(__name__)


def print_debug_args(args):
    logger.debug(f"Verbose: {args.verbose}")
    logger.debug(f"Quiet: {args.quiet}")
    logger.debug(f"Host: {args.host}")
    logger.debug(f"Port: {args.port}")
    logger.debug(f"FILEPATH: {args.dst}")
    logger.debug(f"FILENAME: {args.name}")
    logger.debug(f"Protocol: {args.protocol}")


def main_descarga():
    args = parsear_argumentos_descarga()
    configurar_logger(args.verbose, args.quiet)
    print_debug_args(args)

    Cliente(args.host, args.port, args.protocol).descargar(args.dst, args.name)


if __name__ == "__main__":
    main_descarga()
