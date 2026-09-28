# Estado Actual del archivos src/

### src/download.py

```python
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
```

---

### src/upload.py

```python
import logging

from lib.args import parsear_argumentos_subida
from lib.cliente.mock_cliente import Cliente
from lib.logger import configurar_logger

logger = logging.getLogger(__name__)


def print_debug_args(args):
    logger.debug(f"Verbose: {args.verbose}")
    logger.debug(f"Quiet: {args.quiet}")
    logger.debug(f"Host: {args.host}")
    logger.debug(f"Port: {args.port}")
    logger.debug(f"FILEPATH: {args.src}")
    logger.debug(f"FILENAME: {args.name}")
    logger.debug(f"Protocol: {args.protocol}")


def main_subida():
    args = parsear_argumentos_subida()
    configurar_logger(args.verbose, args.quiet)
    print_debug_args(args)

    Cliente(args.host, args.port, args.protocol).subir(args.src, args.name)


if __name__ == "__main__":
    main_subida()
```

---

### src/start-server.py

```python
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
```

---

### src/lib/logger.py

```python
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
```

---

### src/lib/args.py

```python
import argparse

from lib.constantes import (
    DEFAULT_CLIENT_DIR_DESCARGAS,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SERVER_ALMACENAMIENTO,
    PROTOCOLS,
)


class CustomFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            return super()._format_action_invocation(action)
        return ', '.join(action.option_strings)


def _agregar_argumentos_comunes(parser, is_server=False):
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
    custom_usage = "start-server [-h] [-v | -q] -H ADDR -p PORT -s DIRPATH"
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
    custom_usage = "upload [-h] [-v | -q] -H ADDR -p PORT -s FILEPATH -n FILENAME -r protocol"
    parser = argparse.ArgumentParser(
        prog="upload",
        usage=custom_usage,
        description="< command description >",
        formatter_class=CustomFormatter
    )
    _agregar_argumentos_comunes(parser)
    parser.add_argument("-s", "--src", metavar="FILEPATH", type=str, required=True)
    parser.add_argument("-n", "--name", metavar="FILENAME", type=str, required=True)
    parser.add_argument("-r", "--protocol", metavar="protocol", choices=list(PROTOCOLS), required=True)
    return parser.parse_args(argv)


def parsear_argumentos_descarga(argv=None):
    custom_usage = "download [-h] [-v | -q] -H ADDR -p PORT -d FILEPATH -n FILENAME -r protocol"
    parser = argparse.ArgumentParser(
        prog="download",
        usage=custom_usage,
        description="< command description >",
        formatter_class=CustomFormatter
    )
    _agregar_argumentos_comunes(parser)
    parser.add_argument("-d", "--dst", metavar="FILEPATH", type=str, required=False, default=DEFAULT_CLIENT_DIR_DESCARGAS)
    parser.add_argument("-n", "--name", metavar="FILENAME", type=str, required=True)
    parser.add_argument("-r", "--protocol", metavar="protocol", choices=list(PROTOCOLS), required=True)
    return parser.parse_args(argv)
```

---

### src/lib/constantes.py

```python
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_SERVER_ALMACENAMIENTO = "data/servidor"
DEFAULT_CLIENT_DIR_DESCARGAS = "data/cliente/descargas"
PROTO_SW = 0
PROTO_SACK = 1
PROTOCOLS = {"sw": PROTO_SW, "sack": PROTO_SACK}
```

---

### src/lib/cliente/mock_cliente.py

```python
import logging

logger = logging.getLogger(__name__)


class Cliente:
    def __init__(self, host, port, protocol):
        self._host = host
        self._port = port
        self._protocol = protocol
        logger.debug(f"Cliente creado: {host}:{port}, protocolo={protocol}")

    def descargar(self, dst, name):
        logger.info(f"Descargando {name} -> {dst}")
        print(f"[MOCK] Descargando {name} a {dst}")

    def subir(self, src, name):
        logger.info(f"Subiendo {src} como {name}")
        print(f"[MOCK] Subiendo {src} como {name}")
```

---

### src/lib/servidor/mock_servidor.py

```python
import logging

logger = logging.getLogger(__name__)


class Server:
    def __init__(self, host, port, storage):
        self._host = host
        self._port = port
        self._storage = storage
        logger.debug(f"Server creado: {host}:{port}, storage={storage}")

    def iniciar_servidor(self):
        logger.info(f"Iniciando servidor en {self._host}:{self._port}")
        print(f"[MOCK] Servidor escuchando en {self._host}:{self._port}")
        print(f"[MOCK] Storage: {self._storage}")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self.apagar_servidor()

    def apagar_servidor(self):
        logger.info("Apagando servidor...")
        print("[MOCK] Servidor apagado")
```

---

### src/lib/archivos/errores_archivos.py

```python
"""Errores propios de lectura, escritura y almacenamiento."""


class ErrorArchivo(Exception):
    """Error esperable de una operación de archivos."""


class ErrorArchivoInexistente(ErrorArchivo):
    """El archivo solicitado no existe."""


class ErrorArchivoExistente(ErrorArchivo):
    """Ya hay un archivo definitivo con ese nombre."""


class ErrorTransferenciaEnCurso(ErrorArchivo):
    """El servidor ya está recibiendo un archivo con ese nombre."""


class ErrorNombreArchivo(ErrorArchivo):
    """El nombre no es un nombre de archivo permitido."""


class ErrorTemporalExistente(ErrorArchivo):
    """Ya existe el archivo temporal para ese destino."""


class ErrorLecturaArchivo(ErrorArchivo):
    """No se pudo leer el archivo."""


class ErrorEscrituraArchivo(ErrorArchivo):
    """No se pudo escribir o confirmar el archivo."""


class ErrorEstadoArchivo(ErrorArchivo):
    """Se intentó operar sobre un archivo ya cerrado."""


class ErrorBloqueArchivo(ErrorArchivo):
    """El tamaño o el contenido de un bloque no es válido."""


class ErrorAlmacenamiento(ErrorArchivo):
    """No se pudo preparar el directorio de almacenamiento."""


class ErrorDirectorioDestino(ErrorArchivo):
    """El directorio de destino no es válido o no existe."""
```

---

### src/lib/archivos/archivo_bloques.py

```python
"""Lectura y escritura secuencial de archivos binarios por bloques."""

import os
from pathlib import Path

from lib.archivos.errores_archivos import (
    ErrorArchivoExistente,
    ErrorArchivoInexistente,
    ErrorBloqueArchivo,
    ErrorEscrituraArchivo,
    ErrorEstadoArchivo,
    ErrorLecturaArchivo,
    ErrorTemporalExistente,
)


class LectorArchivo:
    def __init__(self, ruta):
        self.ruta = Path(ruta)
        if not self.ruta.is_file():
            raise ErrorArchivoInexistente(f"No existe el archivo: {self.ruta}")
        try:
            self._archivo = self.ruta.open("rb")
        except OSError as error:
            raise ErrorLecturaArchivo(
                f"No se pudo abrir {self.ruta}: {error}"
            ) from error

    def leer_bloque(self, tamanio):
        if not isinstance(tamanio, int) or tamanio <= 0:
            raise ErrorBloqueArchivo("El tamaño del bloque debe ser positivo")
        if self._archivo.closed:
            raise ErrorEstadoArchivo(f"El archivo está cerrado: {self.ruta}")
        try:
            return self._archivo.read(tamanio)
        except OSError as error:
            raise ErrorLecturaArchivo(
                f"No se pudo leer {self.ruta}: {error}"
            ) from error

    def cerrar(self):
        try:
            self._archivo.close()
        except OSError as error:
            raise ErrorLecturaArchivo(
                f"No se pudo cerrar {self.ruta}: {error}"
            ) from error

    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, traza):
        self.cerrar()


class EscritorArchivo:
    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.ruta_temporal = self.ruta.with_name(self.ruta.name + ".tmp")
        if self.ruta.exists():
            raise ErrorArchivoExistente(f"El archivo ya existe: {self.ruta}")
        if self.ruta_temporal.exists():
            raise ErrorTemporalExistente(
                f"El temporal ya existe: {self.ruta_temporal}"
            )
        try:
            self._archivo = self.ruta_temporal.open("xb")
        except FileExistsError as error:
            raise ErrorTemporalExistente(
                f"El temporal ya existe: {self.ruta_temporal}"
            ) from error
        except OSError as error:
            raise ErrorEscrituraArchivo(
                f"No se pudo crear {self.ruta_temporal}: {error}"
            ) from error
        self._terminado = False

    def escribir_bloque(self, datos):
        if self._terminado:
            raise ErrorEstadoArchivo("La escritura ya terminó")
        if not isinstance(datos, bytes):
            raise ErrorBloqueArchivo("El bloque debe ser de tipo bytes")
        try:
            return self._archivo.write(datos)
        except OSError as error:
            raise ErrorEscrituraArchivo(
                f"No se pudo escribir {self.ruta_temporal}: {error}"
            ) from error

    def confirmar(self):
        if self._terminado:
            raise ErrorEstadoArchivo("La escritura ya terminó")
        try:
            self._archivo.close()
            os.link(self.ruta_temporal, self.ruta)
            self.ruta_temporal.unlink()
        except FileExistsError as error:
            raise ErrorArchivoExistente(
                f"El archivo ya existe: {self.ruta}"
            ) from error
        except OSError as error:
            raise ErrorEscrituraArchivo(
                f"No se pudo confirmar {self.ruta}: {error}"
            ) from error
        self._terminado = True

    def cancelar(self):
        if self._terminado:
            return
        try:
            self._archivo.close()
            self.ruta_temporal.unlink(missing_ok=True)
        except OSError as error:
            raise ErrorEscrituraArchivo(
                f"No se pudo cancelar {self.ruta_temporal}: {error}"
            ) from error
        self._terminado = True

    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, traza):
        if not self._terminado:
            self.cancelar()
```

---

### src/lib/archivos/almacenamiento_servidor.py

```python
"""Reglas del servidor para nombres y subidas, sin lógica de red."""

import threading
from contextlib import contextmanager
from pathlib import Path

from lib.archivos.archivo_bloques import EscritorArchivo, LectorArchivo
from lib.archivos.errores_archivos import (
    ErrorAlmacenamiento,
    ErrorArchivoExistente,
    ErrorNombreArchivo,
    ErrorTransferenciaEnCurso,
)


class AlmacenamientoServidor:
    def __init__(self, directorio):
        self._directorio = Path(directorio)
        try:
            self._directorio.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise ErrorAlmacenamiento(
                f"No se pudo preparar {self._directorio}: {error}"
            ) from error
        if not self._directorio.is_dir():
            raise ErrorAlmacenamiento(
                f"No es un directorio: {self._directorio}"
            )
        self._cerrojo = threading.Lock()
        self._subidas_activas = set()

    def _ruta(self, nombre):
        if (
            not isinstance(nombre, str)
            or not nombre
            or nombre in (".", "..")
            or "/" in nombre
            or "\\" in nombre
            or "\x00" in nombre
            or nombre.endswith(".tmp")
        ):
            raise ErrorNombreArchivo(
                f"Nombre de archivo inválido: {nombre!r}"
            )
        ruta = self._directorio / nombre
        if ruta.is_symlink():
            raise ErrorNombreArchivo(f"No se aceptan enlaces: {nombre}")
        return ruta

    def abrir_descarga(self, nombre):
        return LectorArchivo(self._ruta(nombre))

    @contextmanager
    def recibir_subida(self, nombre):
        ruta = self._ruta(nombre)
        with self._cerrojo:
            if nombre in self._subidas_activas:
                raise ErrorTransferenciaEnCurso(
                    f"Ya se está subiendo el archivo: {nombre}"
                )
            if ruta.exists():
                raise ErrorArchivoExistente(
                    f"El archivo ya existe: {nombre}"
                )
            self._subidas_activas.add(nombre)
        try:
            with EscritorArchivo(ruta) as escritor:
                yield escritor
        finally:
            with self._cerrojo:
                self._subidas_activas.remove(nombre)
```

---

### src/lib/archivos/archivos_cliente.py

```python
"""Validaciones locales del cliente para subir y descargar archivos."""

from pathlib import Path

from lib.archivos.archivo_bloques import EscritorArchivo, LectorArchivo
from lib.archivos.errores_archivos import (
    ErrorDirectorioDestino,
    ErrorNombreArchivo,
)


def abrir_origen_subida(ruta_origen):
    ruta = Path(ruta_origen)
    if ruta.suffix == ".tmp":
        raise ErrorNombreArchivo(f"No se puede subir un temporal: {ruta}")
    return LectorArchivo(ruta)


def preparar_destino_descarga(ruta_destino):
    ruta = Path(ruta_destino)
    if not ruta.parent.is_dir() or ruta.is_dir():
        raise ErrorDirectorioDestino(
            f"El destino debe ser un archivo dentro de un directorio: {ruta}"
        )
    return EscritorArchivo(ruta)
```

---

(End of file)
