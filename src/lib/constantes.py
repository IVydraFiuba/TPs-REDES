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
# Igual que Stop & Wait, el RTO sale del RTT medido.
RTO_MINIMO_SACK = 0.05
# ACK seguidos marcando el mismo agujero antes de reenviarlo sin
# esperar el timeout (retransmision rapida).
ACKS_DUPLICADOS_SACK = 3
# Paciencia del receptor antes de dar al par por muerto. Tiene que
# superar el presupuesto total del emisor, o corta mientras el otro
# todavia esta retransmitiendo. Stop & Wait llega al mismo numero por
# otro camino: espera RTO_MAXIMO_SW en cada uno de sus reintentos.
ESPERA_RECEPCION_SACK = MAX_REINTENTOS_SACK * RTO_MAXIMO_SACK

# Stop & Wait usa el mismo esquema: RTO inicial que se duplica en cada
# timeout hasta el maximo, y un tope de reintentos.
RTO_SW = 1.0
RTO_MAXIMO_SW = 8.0
MAX_REINTENTOS_SW = 10
# El RTO se estima a partir del RTT medido, al estilo de TCP:
#   RTO = SRTT + 4 * DEVRTT
# RTO_SW solo se usa hasta tener la primera muestra. El piso evita
# que una red muy rapida dispare retransmisiones por cualquier
# variacion momentanea.
RTO_MINIMO_SW = 0.05
ALFA_SRTT = 0.125
BETA_DEVRTT = 0.25
K_DEVRTT = 4

# Al cerrar, el canal sigue respondiendo rezagados este tiempo. El ACK
# del ultimo mensaje no lo protege nada: si se pierde y cerramos en el
# acto, el par se queda retransmitiendo hasta agotar sus reintentos.
ESPERA_CIERRE = 0.5

# Tras cerrar una sesion, el servidor sigue contestando los rezagados
# de esa direccion este tiempo. El ACK del ultimo mensaje no lo protege
# nada: si se pierde, el par lo retransmite. Sin esta ventana el
# despachador lo descarta como "sesion desconocida" y el par se queda
# retransmitiendo hasta agotar sus reintentos. Es el TIME_WAIT de TCP.
#
# Tiene que cubrir todo el presupuesto de reintentos del par, por el
# mismo motivo que ESPERA_RECEPCION_SACK: una ventana mas corta vence
# justo antes de que llegue la retransmision que venia a contestar.
# Cuesta una entrada y un datagrama por sesion cerrada.
ESPERA_TIME_WAIT = ESPERA_RECEPCION_SACK

# El SYN viaja antes de que exista el canal, asi que no hereda la
# retransmision de Stop & Wait ni de SACK: necesita la suya.
RTO_SYN = 1.0
RTO_MAXIMO_SYN = 8.0
MAX_REINTENTOS_SYN = 6
