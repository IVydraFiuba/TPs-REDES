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
