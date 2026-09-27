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
