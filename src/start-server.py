import logging
import sys

from lib.archivos.errores_archivos import ErrorAlmacenamiento
from lib.args import parsear_argumentos_servidor
from lib.logger import configurar_logger
from lib.servidor import Servidor

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

    servidor = Servidor(args.host, args.port, args.storage)
    try:
        servidor.iniciar_servidor()
    except ErrorAlmacenamiento as e:
        logger.error("Error de almacenamiento: %s", e)
        return 1
    except OSError as e:
        logger.error("Error de red: %s", e)
        return 1
    except KeyboardInterrupt:
        servidor.apagar_servidor()
    return 0


if __name__ == "__main__":
    sys.exit(main_servidor())
