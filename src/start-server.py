import logging

from lib.args import parsear_argumentos_servidor
from lib.logger import configurar_logger
from lib.servidor.mock_servidor import Server

logger = logging.getLogger(__name__)


def print_debug_args(args):
    logger.debug(f"Verbose: {args.verbose}")
    logger.debug(f"Quiet: {args.quiet}")
    logger.debug(f"Host: {args.host}")
    logger.debug(f"Port: {args.port}")
    logger.debug(f"Storage: {args.storage}")


def main_servidor():
    args = parsear_argumentos_servidor()
    configurar_logger(args.verbose, args.quiet)
    print_debug_args(args)

    Server(args.host, args.port, args.storage).iniciar_servidor()



if __name__ == "__main__":
    main_servidor()
