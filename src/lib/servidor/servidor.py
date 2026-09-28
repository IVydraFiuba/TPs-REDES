"""Servidor UDP para recepción de archivos."""

import logging
import socket
import threading

from lib.archivos.almacenamiento_servidor import AlmacenamientoServidor
from lib.archivos.errores_archivos import ErrorArchivo
from lib.canal.factory import crear_canal
from lib.constantes import (
    PROTO_DIRECTO,
    TAMANIO_BLOQUE,
    TAMANIO_MAX_DATAGRAMA,
    TIMEOUT_SERVIDOR,
)
from lib.protocolo.errores import ErrorMensaje
from lib.protocolo.mensajes import (
    codificar_error,
    codificar_mensaje,
    codificar_respuesta_aceptada,
    decodificar_mensaje,
    decodificar_nombre,
    decodificar_solicitud,
)

logger = logging.getLogger(__name__)


class Servidor:
    def __init__(self, host, port, almacenamiento, protocolo=PROTO_DIRECTO):
        self._host = host
        self._port = port
        self._almacenamiento = AlmacenamientoServidor(almacenamiento)
        self._protocolo = protocolo
        self._detener = threading.Event()
        self._conexion = None
        logger.debug(
            f"Servidor creado: {host}:{port}, storage={almacenamiento}, "
            f"protocolo={protocolo}"
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

                    if tipo == "SOLICITUD_UPLOAD":
                        nombre, tamanio = decodificar_solicitud(carga)
                        logger.info(
                            "Solicitud de upload de %s: %s (%d bytes)",
                            direccion, nombre, tamanio
                        )
                        self._procesar_subida(direccion, nombre, tamanio)

                    elif tipo == "SOLICITUD_DESCARGA":
                        nombre = decodificar_nombre(carga)
                        logger.info(
                            "Solicitud de descarga de %s: %s",
                            direccion, nombre
                        )
                        self._procesar_descarga(direccion, nombre)

                    else:
                        raise ErrorMensaje(
                            f"Tipo de mensaje desconocido: {tipo}"
                        )

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

    def _crear_canal_cliente(self, direccion):
        """Crea un canal para comunicarse con un cliente."""
        return crear_canal(self._protocolo, self._conexion, direccion)

    def _procesar_subida(self, direccion, nombre, tamanio):
        """Procesa una subida de archivo desde un cliente."""
        try:
            with self._almacenamiento.recibir_subida(nombre) as escritor:
                canal = self._crear_canal_cliente(direccion)
                canal.enviar(codificar_mensaje("ACEPTADO"))
                logger.debug("Enviado ACEPTADO a %s", direccion)

                bytes_recibidos = 0
                while True:
                    datos, _ = canal.recibir()
                    tipo, payload = decodificar_mensaje(datos)

                    if tipo == "DATOS":
                        if bytes_recibidos + len(payload) > tamanio:
                            raise ErrorTransferenciaIncompleta(
                                f"Exceso de datos: announced={tamanio}, "
                                f"recibidos+actual={bytes_recibidos + len(payload)}"
                            )
                        escritor.escribir_bloque(payload)
                        bytes_recibidos += len(payload)

                    elif tipo == "FIN" and not payload:
                        if bytes_recibidos != tamanio:
                            raise ErrorTransferenciaIncompleta(
                                f"Bytes incompletos: announced={tamanio}, "
                                f"recibidos={bytes_recibidos}"
                            )
                        escritor.confirmar()
                        canal.enviar(codificar_mensaje("COMPLETADO"))
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

    def _procesar_descarga(self, direccion, nombre):
        """Procesa una descarga de archivo hacia un cliente."""
        try:
            ruta, tamanio = self._almacenamiento.obtener_info_descarga(nombre)
            canal = self._crear_canal_cliente(direccion)
            canal.enviar(codificar_mensaje(
                "ACEPTADO",
                codificar_respuesta_aceptada(tamanio)
            ))
            logger.debug(
                "Enviado ACEPTADO a %s: %s (%d bytes)",
                direccion, nombre, tamanio
            )

            with self._almacenamiento.abrir_descarga(nombre) as lector:
                bytes_enviados = 0
                while True:
                    datos = lector.leer_bloque(TAMANIO_BLOQUE)
                    if not datos:
                        break
                    canal.enviar(codificar_mensaje("DATOS", datos))
                    bytes_enviados += len(datos)

            canal.enviar(codificar_mensaje("FIN"))
            logger.info(
                "Archivo %s enviado completo (%d bytes)",
                nombre, bytes_enviados
            )

            datos, _ = canal.recibir()
            tipo, _ = decodificar_mensaje(datos)
            if tipo != "COMPLETADO":
                logger.warning(
                    "Cliente %s no envió COMPLETADO, llegó: %s",
                    direccion, tipo
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
