# Estado Actual del Proyecto

## Estructura del Proyecto

```
src/
├── upload.py
├── download.py
├── start-server.py
└── lib/
    ├── constantes.py
    ├── utiles/
    │   ├── __init__.py
    │   ├── args.py
    │   └── logger.py
    ├── archivos/
    │   ├── __init__.py
    │   ├── errores_archivos.py
    │   ├── archivo_bloques.py
    │   ├── almacenamiento_servidor.py
    │   └── archivos_cliente.py
    ├── canal/
    │   ├── __init__.py
    │   ├── canal.py
    │   ├── factory.py
    │   ├── segmento.py
    │   ├── udp_directo.py
    │   ├── stopwait.py
    │   └── sack.py
    ├── cliente/
    │   ├── __init__.py
    │   └── cliente.py
    ├── protocolo/
    │   ├── __init__.py
    │   ├── errores.py
    │   └── mensajes.py
    └── servidor/
        ├── __init__.py
        └── servidor.py
```

---

## Protocolos Implementados

| Protocolo | Valor | Estado |
|-----------|-------|--------|
| PROTO_SW | 0 | Stub (no implementado) |
| PROTO_SACK | 1 | Stub (no implementado) |
| PROTO_DIRECTO | 2 | Implementado (UDP sin RDT) |

---

### src/lib/constantes.py

```python
# valores por defecto para el parseo de argumentos
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_SERVER_ALMACENAMIENTO = "data/servidor"
DEFAULT_CLIENT_DIR_DESCARGAS = "data/cliente/descargas"

# Protocol types
PROTO_SW = 0
PROTO_SACK = 1
PROTO_DIRECTO = 2
PROTOCOLS = {"sw": PROTO_SW, "sack": PROTO_SACK, "directo": PROTO_DIRECTO}

# Configuracion canal UDP
TAMANIO_BLOQUE = 1024
TAMANIO_MAX_DATAGRAMA = 1027
TIMEOUT_CLIENTE = 5
TIMEOUT_SERVIDOR = 0.2
```

---

### src/upload.py

```python
import logging
import sys

from lib.archivos.errores_archivos import ErrorArchivo
from lib.utiles.args import parsear_argumentos_subida
from lib.cliente import Cliente
from lib.utiles.logger import configurar_logger
from lib.protocolo.errores import (
    ErrorComunicacion,
    ErrorModoNoImplementado,
    ErrorOperacionRemota,
    ErrorRespuesta,
)

logger = logging.getLogger(__name__)


def main_subida():
    args = parsear_argumentos_subida()
    configurar_logger(args.verbose, args.quiet)
    print_debug_args(args)

    try:
        Cliente(args.host, args.port, args.protocol).subir(args.src, args.name)
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
    except ErrorRespuesta as e:
        logger.error("Respuesta inesperada del servidor: %s", e)
        return 1
    return 0
```

---

### src/download.py

```python
import logging
import sys

from lib.archivos.errores_archivos import ErrorArchivo
from lib.utiles.args import parsear_argumentos_descarga
from lib.cliente import Cliente
from lib.utiles.logger import configurar_logger
from lib.protocolo.errores import (
    ErrorComunicacion,
    ErrorModoNoImplementado,
    ErrorOperacionRemota,
    ErrorRespuesta,
)

logger = logging.getLogger(__name__)


def main_descarga():
    args = parsear_argumentos_descarga()
    configurar_logger(args.verbose, args.quiet)
    print_debug_args(args)

    try:
        Cliente(args.host, args.port, args.protocol).descargar(
            args.dst, args.name
        )
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
    except ErrorRespuesta as e:
        logger.error("Respuesta inesperada del servidor: %s", e)
        return 1
    return 0
```

---

### src/start-server.py

```python
import logging
import sys

from lib.archivos.errores_archivos import ErrorAlmacenamiento
from lib.utiles.args import parsear_argumentos_servidor
from lib.utiles.logger import configurar_logger
from lib.servidor import Servidor

logger = logging.getLogger(__name__)


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
```

---

### src/lib/utiles/logger.py

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

### src/lib/utiles/args.py

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
    parser = argparse.ArgumentParser(
        prog="start-server",
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
    parser = argparse.ArgumentParser(
        prog="upload",
        formatter_class=CustomFormatter
    )
    _agregar_argumentos_comunes(parser)
    parser.add_argument("-s", "--src", metavar="FILEPATH", type=str, required=True)
    parser.add_argument("-n", "--name", metavar="FILENAME", type=str, required=True)
    parser.add_argument(
        "-r", "--protocol",
        metavar="protocol",
        choices=list(PROTOCOLS),
        required=True
    )
    return parser.parse_args(argv)


def parsear_argumentos_descarga(argv=None):
    parser = argparse.ArgumentParser(
        prog="download",
        formatter_class=CustomFormatter
    )
    _agregar_argumentos_comunes(parser)
    parser.add_argument(
        "-d", "--dst",
        metavar="FILEPATH",
        type=str,
        required=False,
        default=DEFAULT_CLIENT_DIR_DESCARGAS
    )
    parser.add_argument("-n", "--name", metavar="FILENAME", type=str, required=True)
    parser.add_argument(
        "-r", "--protocol",
        metavar="protocol",
        choices=list(PROTOCOLS),
        required=True
    )
    return parser.parse_args(argv)
```

---

### src/lib/cliente/cliente.py

```python
"""Cliente UDP para subida y descarga de archivos."""

import json
import logging
import socket

from lib.archivos.archivos_cliente import abrir_origen_subida, preparar_destino_descarga
from lib.archivos.errores_archivos import ErrorArchivo
from lib.canal.factory import crear_canal
from lib.constantes import PROTO_DIRECTO, PROTOCOLS, TAMANIO_BLOQUE
from lib.protocolo.errores import (
    ErrorComunicacion,
    ErrorModoNoImplementado,
    ErrorOperacionRemota,
    ErrorRespuesta,
)
from lib.protocolo.mensajes import (
    codificar_mensaje,
    decodificar_error,
    decodificar_mensaje,
    decodificar_respuesta_aceptada,
)


def parsear_protocolo(protocolo_str):
    """Convierte string de protocolo a valor entero."""
    if protocolo_str not in PROTOCOLS:
        raise ErrorModoNoImplementado(
            f"Protocolo desconocido: {protocolo_str}. "
            f"Opciones: {list(PROTOCOLS.keys())}"
        )
    return PROTOCOLS[protocolo_str]


class Cliente:
    def __init__(self, host, port, protocolo):
        self._host = host
        self._port = port
        self._protocolo = parsear_protocolo(protocolo)
        logger.debug(f"Cliente creado: {host}:{port}, protocolo={protocolo}")

    def subir(self, origen, nombre):
        """Sube un archivo al servidor usando PROTO_DIRECTO."""
        if self._protocolo != PROTO_DIRECTO:
            raise ErrorModoNoImplementado(...)
        # Usa crear_canal() para obtener el canal apropiado
        # Envía mensajes de aplicación con codificar_mensaje()
        # Lee respuestas con decodificar_mensaje()

    def descargar(self, destino, nombre):
        """Descarga un archivo del servidor usando PROTO_DIRECTO."""
        if self._protocolo != PROTO_DIRECTO:
            raise ErrorModoNoImplementado(...)
        # Usa crear_canal() para obtener el canal apropiado
        # Solicita y recibe archivo por bloques
```

---

### src/lib/servidor/servidor.py

```python
"""Servidor UDP para recepción de archivos."""

import logging
import socket
import threading

from lib.archivos.almacenamiento_servidor import AlmacenamientoServidor
from lib.archivos.errores_archivos import ErrorArchivo
from lib.canal.factory import crear_canal
from lib.constantes import PROTO_DIRECTO, TAMANIO_BLOQUE, TIMEOUT_SERVIDOR
from lib.protocolo.mensajes import (
    codificar_error,
    codificar_mensaje,
    codificar_respuesta_aceptada,
    decodificar_mensaje,
    decodificar_nombre,
    decodificar_solicitud,
)


class Servidor:
    def __init__(self, host, port, almacenamiento, protocolo=PROTO_DIRECTO):
        self._host = host
        self._port = port
        self._almacenamiento = AlmacenamientoServidor(almacenamiento)
        self._protocolo = protocolo
        self._detener = threading.Event()
        self._conexion = None

    def iniciar_servidor(self):
        """Loop principal: recibe datagramas y procesa SOLICITUD_UPLOAD o SOLICITUD_DESCARGA."""

    def _crear_canal_cliente(self, direccion):
        """Factory method para crear canal según protocolo."""
        return crear_canal(self._protocolo, self._conexion, direccion)

    def _procesar_subida(self, direccion, nombre, tamanio):
        """Recibe archivo del cliente y lo guarda."""

    def _procesar_descarga(self, direccion, nombre):
        """Envía archivo al cliente."""

    def apagar_servidor(self):
        """Detiene el servidor."""
```

---

### src/lib/canal/canal.py

```python
"""Interfaz abstracta para canales de transporte."""

from abc import ABC, abstractmethod


class Canal(ABC):
    """Contrato:
        - enviar(bytes): envía datos al peer
        - recibir() -> (bytes, direccion): recibe datos del peer
        - cerrar(): cierra el canal ordenadamente
    """

    @abstractmethod
    def enviar(self, datos):
        pass

    @abstractmethod
    def recibir(self):
        pass

    def cerrar(self):
        pass
```

---

### src/lib/canal/segmento.py

```python
"""Formato de segmento para la capa de transporte."""

import struct
from collections import namedtuple

DATA = 0
ACK = 1
SYN = 2
FIN = 3

_CABECERA = struct.Struct("!BIH")
TAM_CABECERA = _CABECERA.size  # 7 bytes

Segmento = namedtuple("Segmento", ["tipo", "seq", "payload"])
MAX_PAYLOAD = 1024


def empaquetar(tipo, seq, payload=b""):
    """Codifica segmento: cabecera(7) + payload"""
    return _CABECERA.pack(tipo, seq, len(payload)) + payload


def desempaquetar(datos):
    """Decodifica segmento a Segmento(tipo, seq, payload)"""
```

---

### src/lib/canal/factory.py

```python
"""Factory para crear canales según protocolo."""

from lib.constantes import PROTO_DIRECTO, PROTO_SACK, PROTO_SW


def crear_canal(protocolo, conexion, direccion):
    """Retorna Canal apropiado según protocolo."""
    if protocolo == PROTO_DIRECTO:
        from .udp_directo import CanalUdpDirecto
        return CanalUdpDirecto(conexion, direccion)
    if protocolo == PROTO_SW:
        from .stopwait import CanalStopWait
        return CanalStopWait(conexion, direccion)
    if protocolo == PROTO_SACK:
        from .sack import CanalSack
        return CanalSack(conexion, direccion)
    raise ErrorModoNoImplementado(...)
```

---

### src/lib/canal/udp_directo.py

```python
"""Canal UDP directo - modo mock temporal (sin RDT)."""

import socket

from lib.constantes import TAMANIO_MAX_DATAGRAMA, TIMEOUT_CLIENTE
from lib.protocolo.errores import ErrorComunicacion, ErrorTiempoEspera

from .canal import Canal


class CanalUdpDirecto(Canal):
    """Implementación directa de UDP sin confiabilidad."""

    def enviar(self, datos):
        self._conexion.sendto(datos, self._direccion)

    def recibir(self):
        self._conexion.settimeout(TIMEOUT_CLIENTE)
        datos, direccion = self._conexion.recvfrom(TAMANIO_MAX_DATAGRAMA)
        return datos, direccion

    def cerrar(self):
        self._conexion.close()
```

---

### src/lib/protocolo/mensajes.py

```python
"""Mensajes del protocolo de aplicación."""

import json
import struct

_TIPOS = {
    "SOLICITUD_UPLOAD": 1,
    "ACEPTADO": 2,
    "DATOS": 3,
    "FIN": 4,
    "COMPLETADO": 5,
    "ERROR": 6,
    "SOLICITUD_DESCARGA": 7,
}


def codificar_mensaje(tipo, carga=b""):
    """Codifica mensaje con cabecera de 3 bytes (tipo:1, longitud:2)."""
    return struct.pack("!BH", _TIPOS[tipo], len(carga)) + carga


def decodificar_mensaje(datagrama):
    """Decodifica mensaje. Retorna (nombre_tipo, carga)."""


def codificar_solicitud(nombre, tamanio, modo="directo"):
    """JSON: {"nombre": ..., "tamanio": ..., "modo": ...}"""


def codificar_error(codigo, detalle):
    """JSON: {"codigo": ..., "detalle": ...}"""


def codificar_respuesta_aceptada(tamanio):
    """JSON: {"tamanio": ...}"""


def decodificar_respuesta_aceptada(carga):
    """Retorna tamanio desde JSON."""
```

---

### src/lib/protocolo/errores.py

```python
"""Errores del protocolo de aplicación."""


class ErrorProtocolo(Exception): pass
class ErrorMensaje(ErrorProtocolo): pass
class ErrorComunicacion(ErrorProtocolo): pass
class ErrorTiempoEspera(ErrorComunicacion): pass
class ErrorServidorOcupado(ErrorComunicacion): pass
class ErrorModoNoImplementado(ErrorProtocolo): pass
class ErrorOperacionRemota(ErrorProtocolo): pass
class ErrorRespuesta(ErrorProtocolo): pass
class ErrorTransferenciaIncompleta(ErrorProtocolo): pass
```

---

### src/lib/archivos/errores_archivos.py

```python
"""Errores de operaciones de archivos."""


class ErrorArchivo(Exception): pass
class ErrorArchivoInexistente(ErrorArchivo): pass
class ErrorArchivoExistente(ErrorArchivo): pass
class ErrorTransferenciaEnCurso(ErrorArchivo): pass
class ErrorNombreArchivo(ErrorArchivo): pass
class ErrorTemporalExistente(ErrorArchivo): pass
class ErrorLecturaArchivo(ErrorArchivo): pass
class ErrorEscrituraArchivo(ErrorArchivo): pass
class ErrorEstadoArchivo(ErrorArchivo): pass
class ErrorBloqueArchivo(ErrorArchivo): pass
class ErrorAlmacenamiento(ErrorArchivo): pass
class ErrorDirectorioDestino(ErrorArchivo): pass
```

---

### src/lib/archivos/archivo_bloques.py

```python
"""Lectura/escritura secuencial de archivos por bloques."""

class LectorArchivo:
    """Lee archivos por bloques usando context manager."""

    def leer_bloque(self, tamanio):
        """Retorna hasta tamanio bytes; b'' indica EOF."""

    def cerrar(self): pass

    def __enter__(self): return self
    def __exit__(self, *args): self.cerrar()


class EscritorArchivo:
    """Escribe a .tmp, confirma o cancela al cerrar."""

    def escribir_bloque(self, datos): pass
    def confirmar(self): pass  # Renombra .tmp -> definitivo
    def cancelar(self): pass     # Elimina .tmp

    def __enter__(self): return self
    def __exit__(self, *args):
        if not self._terminado:
            self.cancelar()
```

---

### src/lib/archivos/almacenamiento_servidor.py

```python
"""Gestión de archivos en el servidor."""


class AlmacenamientoServidor:
    """Thread-safe con cerrojo y conjunto de subidas activas."""

    def abrir_descarga(self, nombre):
        """Retorna LectorArchivo para el nombre."""

    def obtener_info_descarga(self, nombre):
        """Retorna (ruta, tamanio). Lanza ErrorArchivoInexistente si no existe."""

    @contextmanager
    def recibir_subida(self, nombre):
        """Reserva nombre, retorna EscritorArchivo. Cancela si sale sin confirmar."""
```

---

### src/lib/archivos/archivos_cliente.py

```python
"""Validaciones del cliente para subir/descargar."""


def abrir_origen_subida(ruta_origen):
    """Valida y retorna LectorArchivo. Rechaza archivos .tmp."""


def preparar_destino_descarga(ruta_destino):
    """Valida y retorna EscritorArchivo. El destino debe ser archivo en directorio existente."""
```

---

## Capas del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│  Aplicación (Cliente / Servidor)                          │
│  - Mensajes: SOLICITUD_UPLOAD, ACEPTADO, DATOS, FIN...  │
│  - Usa: codificar_mensaje(), decodificar_mensaje()      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Transporte (Canal) - ABC                                 │
│  - Interfaz: enviar(bytes), recibir() -> (bytes, addr)  │
│  - Implementaciones: UDP Directo, Stop&Wait, SACK        │
│  - Usa: crear_canal() factory                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Red (socket UDP)                                        │
│  - Datagramas planos                                     │
└─────────────────────────────────────────────────────────────┘
```

## Protocolo de Aplicación

### Upload

```
Cliente                              Servidor
SOLICITUD_UPLOAD(nombre, tamaño) -> reserva nombre
                             <- ACEPTADO
DATOS(bytes)                 -> escribe bloque
DATOS(bytes)                 -> escribe bloque
FIN                          -> comprueba, confirma
                             <- COMPLETADO
```

### Download

```
Cliente                              Servidor
SOLICITUD_DESCARGA(nombre)    ->
                             <- ACEPTADO(tamaño)
                       DATOS(bytes) ->
                       DATOS(bytes) ->
                       FIN           ->
COMPLETADO                ->
```

---

(End of file)
