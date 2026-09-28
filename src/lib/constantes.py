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

# Configuracion canal UDP (mock)
TAMANIO_BLOQUE = 1024
TAMANIO_MAX_DATAGRAMA = 1027
TIMEOUT_CLIENTE = 5
TIMEOUT_SERVIDOR = 0.2
