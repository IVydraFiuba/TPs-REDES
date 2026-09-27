# lib/logger.py
import logging


def configurar_logger(verbose, quiet):
    if quiet:
        nivel = logging.ERROR
    elif verbose:
        nivel = logging.DEBUG
    else:
        nivel = logging.INFO

    logging.basicConfig(
        level=nivel,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
