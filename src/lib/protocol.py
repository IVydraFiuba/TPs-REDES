# lib/protocol.py
import logging
import socket
import struct

from lib.constants import (
    BUFFER_SIZE,
    ENCODING,
    ERR_OK,
    MAX_FILENAME_LEN,
    MAX_RETRIES,
    TIMEOUT,
)

logger = logging.getLogger(__name__)

_FORMATO = "!BBIB"
_FORMATO_RESP = "!BI"


def conectar(server_addr, opcode, protocolo, filename, filesize):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    pedido = _empaquetar_handshake(opcode, protocolo, filesize, filename)
    sock.settimeout(TIMEOUT)

    for intento in range(MAX_RETRIES):
        sock.sendto(pedido, server_addr)
        try:
            datos, server_data_addr = sock.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            logger.debug(f"saludo sin respuesta, reintento {intento + 1}")
            continue

        try:
            status, filesize_resp = _desempaquetar_respuesta(datos)
        except ValueError:
            logger.debug("respuesta invalida, la descarto")
            continue

        if status != ERR_OK:
            sock.close()
            raise ConnectionError(f"handshake rechazado: status={status}")
        logger.debug(f"conectado; datos por {server_data_addr}")
        return sock, server_data_addr, filesize_resp

    sock.close()
    raise ConnectionError("el servidor no respondio")


def recibir_handshake(listen_sock):
    datos, client_addr = listen_sock.recvfrom(BUFFER_SIZE)
    opcode, protocolo, filesize, filename = _desempaquetar_handshake(datos)
    return opcode, protocolo, filesize, filename, client_addr


def responder_handshake(listen_sock, client_addr, status, filesize=0):
    respuesta = _empaquetar_respuesta(status, filesize)
    if status != ERR_OK:
        listen_sock.sendto(respuesta, client_addr)
        return None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 0))
    sock.sendto(respuesta, client_addr)
    return sock


def _empaquetar_handshake(opcode, protocolo, filesize, filename):
    nombre = filename.encode(ENCODING)
    if len(nombre) > MAX_FILENAME_LEN:
        raise ValueError("nombre de archivo demasiado largo")
    cabecera = struct.pack(_FORMATO, opcode, protocolo, filesize, len(nombre))
    return cabecera + nombre


def _desempaquetar_handshake(datos):
    tam = struct.calcsize(_FORMATO)
    if len(datos) < tam:
        raise ValueError("handshake incompleto")
    opcode, protocolo, filesize, largo = struct.unpack(_FORMATO, datos[:tam])
    nombre = datos[tam:tam + largo]
    if len(nombre) != largo:
        raise ValueError("nombre de archivo truncado")
    return opcode, protocolo, filesize, nombre.decode(ENCODING)


def _empaquetar_respuesta(status, filesize=0):
    return struct.pack(_FORMATO_RESP, status, filesize)


def _desempaquetar_respuesta(datos):
    if len(datos) != struct.calcsize(_FORMATO_RESP):
        raise ValueError("respuesta de handshake invalida")
    status, filesize = struct.unpack(_FORMATO_RESP, datos)
    return status, filesize
