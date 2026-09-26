# lib/protocol.py
import struct
import socket

from lib.constants import (
    ENCODING,
    MAX_FILENAME_LEN,
    BUFFER_SIZE,
    ERR_OK,
    TIMEOUT,
    MAX_RETRIES,
)

# opcode, protocolo, filesize, largo_del_nombre
_FORMATO = "!BBIB"

# status del servidor + filesize (usado en DOWNLOAD)
_FORMATO_RESP = "!BI"

# Orquestacion de la conexion


def conectar(server_addr, opcode, protocolo, filename, filesize, logger):
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
    """Responde el handshake y devuelve el socket de datos.

    Si el pedido se acepta, crea el socket propio de la sesion y
    responde desde ahi, para que el cliente aprenda a que puerto
    mandar. Si se rechaza, responde por el socket de escucha y
    devuelve None: una sesion rechazada no necesita socket propio.
    """
    respuesta = _empaquetar_respuesta(status, filesize)
    if status != ERR_OK:
        listen_sock.sendto(respuesta, client_addr)
        return None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 0))
    sock.sendto(respuesta, client_addr)
    return sock

# Handshake


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

# Respuesta del handshake


def _empaquetar_respuesta(status, filesize=0):
    return struct.pack(_FORMATO_RESP, status, filesize)


def _desempaquetar_respuesta(datos):
    if len(datos) != struct.calcsize(_FORMATO_RESP):
        raise ValueError("respuesta de handshake invalida")
    status, filesize = struct.unpack(_FORMATO_RESP, datos)
    return status, filesize
