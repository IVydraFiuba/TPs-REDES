"""Servidor UDP para recepción de archivos."""

import logging
import socket
import threading

from lib.archivos.almacenamiento_servidor import AlmacenamientoServidor
from lib.archivos.errores_archivos import ErrorArchivo
from lib.canal.udp_directo import CanalUdpDirecto
from lib.constantes import TAMANIO_MAX_DATAGRAMA, TIMEOUT_SERVIDOR
from lib.protocolo.errores import ErrorMensaje
from lib.protocolo.mensajes import (
    codificar_error,
    codificar_mensaje,
    decodificar_mensaje,
    decodificar_solicitud,
)

logger = logging.getLogger(__name__)


class Servidor:
    def __init__(self, host, port, almacenamiento, clase_canal=CanalUdpDirecto):
        self._host = host
        self._port = port
        self._almacenamiento = AlmacenamientoServidor(almacenamiento)
        self._clase_canal = clase_canal
        self._detener = threading.Event()
        self._conexion = None
        logger.debug(
            f"Servidor creado: {host}:{port}, storage={almacenamiento}"
        )

    def iniciar_servidor(self):
        """Inicia el servidor y atiende solicitudes hasta Ctrl+C."""
        self._conexion = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._conexion.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._conexion.bind((self._host, self._port))
        self._conexion.settimeout(TIMEOUT_SERVIDOR)
        logger.info(f"Servidor escuchando en {self._host}:{self._port}")

        try:
            while not self._detener.is_set():
                try:
                    datagrama, direccion = self._conexion.recvfrom(
                        TAMANIO_MAX_DATAGRAMA
                    )
                except socket.timeout:
                    continue

                try:
                    tipo, carga = decodificar_mensaje(datagrama)
                    if tipo != "SOLICITUD_UPLOAD":
                        raise ErrorMensaje(
                            f"Se esperaba SOLICITUD_UPLOAD, llegó {tipo}"
                        )

                    nombre, tamanio = decodificar_solicitud(carga)
                    logger.info(
                        "Solicitud de %s: %s (%d bytes)",
                        direccion, nombre, tamanio
                    )
                    self._procesar_subida(direccion, nombre, tamanio)

                except (ErrorArchivo, ErrorMensaje) as e:
                    logger.warning("Error de %s: %s", direccion, e)
                    try:
                        self._conexion.sendto(
                            codificar_mensaje(
                                "ERROR",
                                codificar_error(type(e).__name__, str(e))
                            ),
                            direccion
                        )
                    except OSError:
                        logger.exception(
                            "No se pudo informar el error a %s", direccion
                        )

        finally:
            self._conexion.close()
            logger.info("Servidor detenido")

    def _procesar_subida(self, direccion, nombre, tamanio):
        """Procesa una subida de archivo desde un cliente."""
        try:
            with self._almacenamiento.recibir_subida(nombre) as escritor:
                canal = self._clase_canal(self._conexion, direccion)
                canal.enviar("ACEPTADO")
                logger.debug("Enviado ACEPTADO a %s", direccion)

                bytes_recibidos = 0
                while True:
                    tipo, datos = canal.recibir()

                    if tipo == "DATOS":
                        if bytes_recibidos + len(datos) > tamanio:
                            raise ErrorTransferenciaIncompleta(
                                f"Exceso de datos: announced={tamanio}, "
                                f"recibidos+actual={bytes_recibidos + len(datos)}"
                            )
                        escritor.escribir_bloque(datos)
                        bytes_recibidos += len(datos)

                    elif tipo == "FIN" and not datos:
                        if bytes_recibidos != tamanio:
                            raise ErrorTransferenciaIncompleta(
                                f"Bytes incompletos: announced={tamanio}, "
                                f"recibidos={bytes_recibidos}"
                            )
                        escritor.confirmar()
                        canal.enviar("COMPLETADO")
                        logger.info(
                            "Archivo %s recibido completo (%d bytes)",
                            nombre, bytes_recibidos
                        )
                        return

                    else:
                        raise ErrorMensaje(
                            f"Mensaje inesperado: {tipo}"
                        )

        except ErrorArchivo as e:
            logger.error("Error de archivo procesando %s: %s", nombre, e)
            try:
                self._conexion.sendto(
                    codificar_mensaje(
                        "ERROR",
                        codificar_error(type(e).__name__, str(e))
                    ),
                    direccion
                )
            except OSError:
                pass

    def apagar_servidor(self):
        """Detiene el servidor de forma ordenada."""
        logger.info("Apagando servidor...")
        self._detener.set()


class ErrorTransferenciaIncompleta(ErrorArchivo):
    """La cantidad de bytes recibidos no coincide con lo anunciado."""
