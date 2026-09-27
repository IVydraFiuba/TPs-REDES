import argparse

from lib.constantes import (
    DEFAULT_CLIENT_DIR_DESCARGAS,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SERVER_ALMACENAMIENTO,
    PROTOCOLS,
)


class CustomFormatter(argparse.HelpFormatter):
    """Formateador personalizado para evitar que el metavar se repita."""

    def _format_action_invocation(self, action):
        if not action.option_strings:
            return super()._format_action_invocation(action)
        return ', '.join(action.option_strings)


def _agregar_argumentos_comunes(parser, is_server=False):
    """Agrega al parser los argumentos compartidos por todos los comandos."""
    parser._optionals.title = "arguments"

    grupo_logging = parser.add_mutually_exclusive_group()
    grupo_logging.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="increase output verbosity"
    )
    grupo_logging.add_argument(
        "-q", "--quiet",
        action="store_true",
        default=False,
        help="decrease output verbosity"
    )

    host_help = "service IP address" if is_server else "server IP address"
    port_help = "service port" if is_server else "server port"

    parser.add_argument(
        "-H", "--host",
        metavar="ADDR",
        type=str,
        required=False,
        default=DEFAULT_HOST,
        help=f"{host_help} (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "-p", "--port",
        metavar="PORT",
        type=int,
        required=False,
        default=DEFAULT_PORT,
        help=f"{port_help} (default: {DEFAULT_PORT})"
    )


def parsear_argumentos_servidor(argv=None):
    """Parsea y valida los argumentos del comando start-server."""
    custom_usage = (
        "start-server [-h] [-v | -q] -H ADDR -p PORT -s DIRPATH"
    )
    parser = argparse.ArgumentParser(
        prog="start-server",
        usage=custom_usage,
        description="< command description >",
        formatter_class=CustomFormatter
    )
    _agregar_argumentos_comunes(parser, is_server=True)
    parser.add_argument(
        "-s", "--storage",
        metavar="DIRPATH",
        type=str,
        required=False,
        default=DEFAULT_SERVER_ALMACENAMIENTO,
        help=f"storage dir path (default: {DEFAULT_SERVER_ALMACENAMIENTO})"
    )
    return parser.parse_args(argv)


def parsear_argumentos_subida(argv=None):
    """Parsea y valida los argumentos del comando upload."""
    custom_usage = (
        "upload [-h] [-v | -q] -H ADDR -p PORT"
        " -s FILEPATH -n FILENAME -r protocol"
    )
    parser = argparse.ArgumentParser(
        prog="upload",
        usage=custom_usage,
        description="< command description >",
        formatter_class=CustomFormatter
    )
    _agregar_argumentos_comunes(parser)
    parser.add_argument(
        "-s", "--src",
        metavar="FILEPATH",
        type=str,
        required=True,
        help="source file path"
    )
    parser.add_argument(
        "-n", "--name",
        metavar="FILENAME",
        type=str,
        required=True,
        help="file name"
    )
    parser.add_argument(
        "-r", "--protocol",
        metavar="protocol",
        choices=list(PROTOCOLS),
        required=True,
        help="error recovery protocol"
    )
    return parser.parse_args(argv)


def parsear_argumentos_descarga(argv=None):
    """Parsea y valida los argumentos del comando download."""
    custom_usage = (
        "download [-h] [-v | -q] -H ADDR -p PORT"
        " -d FILEPATH -n FILENAME -r protocol"
    )
    parser = argparse.ArgumentParser(
        prog="download",
        usage=custom_usage,
        description="< command description >",
        formatter_class=CustomFormatter
    )
    _agregar_argumentos_comunes(parser)
    parser.add_argument(
        "-d", "--dst",
        metavar="FILEPATH",
        type=str,
        required=False,
        default=DEFAULT_CLIENT_DIR_DESCARGAS,
        help=f"destination file path (default: {DEFAULT_CLIENT_DIR_DESCARGAS})"
    )
    parser.add_argument(
        "-n", "--name",
        metavar="FILENAME",
        type=str,
        required=True,
        help="file name"
    )
    parser.add_argument(
        "-r", "--protocol",
        metavar="protocol",
        choices=list(PROTOCOLS),
        required=True,
        help="error recovery protocol"
    )
    return parser.parse_args(argv)
