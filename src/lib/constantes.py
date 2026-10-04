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

# Presupuesto de bytes: datagrama UDP > segmento > mensaje > bloque.
TAMANIO_MAX_DATAGRAMA = 1400
TAMANIO_CABECERA_SEGMENTO = 11
TAMANIO_CABECERA_MENSAJE = 3
TAMANIO_MAX_CARGA_SEGMENTO = TAMANIO_MAX_DATAGRAMA - TAMANIO_CABECERA_SEGMENTO
TAMANIO_BLOQUE = TAMANIO_MAX_CARGA_SEGMENTO - TAMANIO_CABECERA_MENSAJE

# Tiempos de infraestructura. Los futuros canales confiables definirán su RTO.
TIMEOUT_INACTIVIDAD_SESION = 5
TIMEOUT_DESPACHADOR = 0.2

# Recursos del servidor concurrente.
TAMANIO_BUFFER_RECEPCION_UDP = 8 * 1024 * 1024
CAPACIDAD_COLA_SESION = 4096
MAXIMO_SESIONES = 50

# Tiempo de espera para retransmisión de un segmento en Sack.
RTO_SACK = 1.0
# Tope del backoff: el RTO se duplica en cada timeout hasta este valor.
RTO_MAXIMO_SACK = 8.0
# Segmentos sin confirmar que se permiten en vuelo a la vez.
VENTANA_SACK = 64
# Rondas seguidas sin que avance la ventana antes de dar por muerto al par.
MAX_REINTENTOS_SACK = 10

# Stop & Wait usa el mismo esquema: RTO inicial que se duplica en cada
# timeout hasta el maximo, y un tope de reintentos.
RTO_SW = 1.0
RTO_MAXIMO_SW = 8.0
MAX_REINTENTOS_SW = 10
