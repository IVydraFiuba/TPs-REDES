import logging
import sys
from pathlib import Path

from lib.archivos.errores_archivos import ErrorArchivo
from lib.capas.pca.errores import ErrorMensaje, ErrorOperacionRemota
from lib.capas.rdt.errores import ErrorModoNoImplementado, ErrorSegmento
from lib.capas.udp.errores import ErrorComunicacion
from lib.cliente import Cliente
from lib.utiles.args import parsear_argumentos_descarga
from lib.utiles.logger import configurar_logger

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

    try:
        destino = Path(args.dst)
        if destino.is_dir():
            destino = destino / args.name
        Cliente(args.host, args.port, args.protocol).descargar(
            destino, args.name
        )
    except OSError as e:
        logger.error("Error al preparar destino: %s", e)
        return 1
    except ErrorModoNoImplementado as e:
        logger.error("Modo no implementado: %s", e)
        return 1
    except ErrorArchivo as e:
        logger.error("Error de archivo: %s", e)
        return 1
    except ErrorComunicacion as e:
        logger.error("Error de comunicación: %s", e)
        return 1
    except ErrorOperacionRemota as e:
        logger.error("Error del servidor: %s", e)
        return 1
    except (ErrorMensaje, ErrorSegmento) as e:
        logger.error("Respuesta inesperada del servidor: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main_descarga())
