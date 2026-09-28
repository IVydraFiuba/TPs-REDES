"""Cliente UDP para subida y descarga de archivos."""

import logging
import socket

from lib.archivos.archivos_cliente import abrir_origen_subida
from lib.archivos.errores_archivos import ErrorArchivo
from lib.canal.udp_directo import CanalUdpDirecto
from lib.constantes import PROTO_DIRECTO, TAMANIO_BLOQUE
from lib.protocolo.errores import (
    ErrorComunicacion,
    ErrorModoNoImplementado,
    ErrorOperacionRemota,
    ErrorRespuesta,
)
from lib.protocolo.mensajes import (
    codificar_mensaje,
    codificar_solicitud,
    decodificar_error,
    decodificar_mensaje,
)

logger = logging.getLogger(__name__)


class Cliente:
    def __init__(self, host, port, protocolo):
        self._host = host
        self._port = port
        self._protocolo = protocolo
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

                solicitud = codificar_solicitud(nombre, tamanio)
                canal.enviar_datagrama(solicitud)
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
        """Descarga un archivo del servidor. No implementado."""
        raise ErrorModoNoImplementado(
            "Descarga aún no implementada. "
            "Solo 'subir' está disponible en modo 'directo'."
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
