"""Cliente UDP para subida y descarga de archivos."""

import json
import logging
import socket

from lib.archivos.archivos_cliente import abrir_origen_subida, preparar_destino_descarga
from lib.archivos.errores_archivos import ErrorArchivo
from lib.canal.udp_directo import CanalUdpDirecto
from lib.constantes import (
    PROTO_DIRECTO,
    PROTO_SACK,
    PROTO_SW,
    PROTOCOLS,
    TAMANIO_BLOQUE,
)
from lib.protocolo.errores import (
    ErrorComunicacion,
    ErrorModoNoImplementado,
    ErrorOperacionRemota,
    ErrorRespuesta,
)
from lib.protocolo.mensajes import (
    codificar_mensaje,
    decodificar_error,
    decodificar_respuesta_aceptada,
)

logger = logging.getLogger(__name__)


def parsear_protocolo(protocolo_str):
    """Convierte string de protocolo ('sw', 'sack', 'directo') a valor entero."""
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
        """Sube un archivo al servidor usando el protocolo directo."""
        if self._protocolo != PROTO_DIRECTO:
            raise ErrorModoNoImplementado(
                f"Protocolo {self._protocolo} no implementado. "
                "Usar 'directo' para pruebas."
            )

        with abrir_origen_subida(origen) as lector:
            tamanio = lector.ruta.stat().st_size
            logger.info(
                "Iniciando subida: %s como %s (%d bytes)",
                origen, nombre, tamanio
            )

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
                canal = CanalUdpDirecto(conexion, (self._host, self._port))

                solicitud = json.dumps(
                    {"nombre": nombre, "tamanio": tamanio, "modo": "directo"}
                ).encode("utf-8")
                canal.enviar("SOLICITUD_UPLOAD", solicitud)
                logger.debug("Solicitud enviada: %s", nombre)

                self._esperar_respuesta(canal, "ACEPTADO")
                logger.debug("Servidor aceptó la solicitud")

                bytes_enviados = 0
                while True:
                    datos = lector.leer_bloque(TAMANIO_BLOQUE)
                    if not datos:
                        break
                    canal.enviar("DATOS", datos)
                    bytes_enviados += len(datos)

                logger.debug("Enviados %d bytes, enviando FIN", bytes_enviados)
                canal.enviar("FIN")

                self._esperar_respuesta(canal, "COMPLETADO")
                logger.info(
                    "Subida completada: %s (%d bytes)", nombre, bytes_enviados
                )

    def descargar(self, destino, nombre):
        """Descarga un archivo del servidor usando el protocolo directo."""
        if self._protocolo != PROTO_DIRECTO:
            raise ErrorModoNoImplementado(
                f"Protocolo {self._protocolo} no implementado. "
                "Usar 'directo' para pruebas."
            )

        logger.info(
            "Iniciando descarga: %s -> %s",
            nombre, destino
        )

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            canal = CanalUdpDirecto(conexion, (self._host, self._port))

            solicitud = json.dumps({"nombre": nombre}).encode("utf-8")
            canal.enviar("SOLICITUD_DESCARGA", solicitud)
            logger.debug("Solicitud enviada: %s", nombre)

            tipo, carga = canal.recibir()
            if tipo == "ERROR":
                codigo, detalle = decodificar_error(carga)
                logger.warning("Error del servidor: %s - %s", codigo, detalle)
                raise ErrorOperacionRemota(f"{codigo}: {detalle}")

            if tipo != "ACEPTADO":
                raise ErrorRespuesta(
                    f"Respuesta inesperada: se esperaba ACEPTADO, llegó {tipo}"
                )

            tamanio = decodificar_respuesta_aceptada(carga)
            logger.debug("Servidor aceptó, tamaño: %d bytes", tamanio)

            with preparar_destino_descarga(destino) as escritor:
                bytes_recibidos = 0
                while True:
                    tipo, datos = canal.recibir()

                    if tipo == "DATOS":
                        escritor.escribir_bloque(datos)
                        bytes_recibidos += len(datos)
                        logger.debug(
                            "Recibido bloque: %d bytes (total: %d/%d)",
                            len(datos), bytes_recibidos, tamanio
                        )

                    elif tipo == "FIN" and not datos:
                        logger.debug(
                            "Descarga completada: %d/%d bytes",
                            bytes_recibidos, tamanio
                        )
                        escritor.confirmar()
                        canal.enviar("COMPLETADO")
                        logger.info(
                            "Descarga completada: %s (%d bytes)",
                            nombre, bytes_recibidos
                        )
                        return

                    else:
                        raise ErrorRespuesta(
                            f"Mensaje inesperado: {tipo}"
                        )

    def _esperar_respuesta(self, canal, esperado):
        """Espera un mensaje del servidor. Maneja errores."""
        try:
            tipo, carga = canal.recibir()
        except ErrorComunicacion as e:
            logger.error("Error de comunicación: %s", e)
            raise

        if tipo == "ERROR":
            codigo, detalle = decodificar_error(carga)
            logger.warning("Error del servidor: %s - %s", codigo, detalle)
            raise ErrorOperacionRemota(f"{codigo}: {detalle}")

        if tipo != esperado or carga:
            raise ErrorRespuesta(
                f"Respuesta inesperada: se esperaba {esperado}, "
                f"llegó {tipo}"
            )
