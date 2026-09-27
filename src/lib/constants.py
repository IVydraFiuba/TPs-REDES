OP_UPLOAD = 0
OP_DOWNLOAD = 1
PROTO_SW = 0
PROTO_SACK = 1
PROTOCOLS = {"sw": PROTO_SW, "sack": PROTO_SACK}
ERR_OK = 0
ERR_FILE_NOT_FOUND = 1
ERR_FILE_EXISTS = 2
ERR_NO_SPACE = 3
ERR_PERMISSION = 4
ERR_INVALID_PROTOCOL = 5
ERR_INVALID_OPCODE = 6
PAYLOAD_SIZE = 1024
BUFFER_SIZE = 2048
TIMEOUT = 0.5
WINDOW_SIZE = 100
MAX_RETRIES = 10

# Cierre del emisor: cuantos FIN manda y cada cuantos segundos
FIN_REINTENTOS = 3
FIN_ESPERA = 0.2

# Segundos que el receptor sigue respondiendo duplicados antes de cerrar
ESPERA_CIERRE = 2.0

# ACK duplicados sobre el mismo agujero que disparan retransmision
# inmediata en SACK, sin esperar el timeout
ACKS_DUP_RETRANSMISION = 3

ENCODING = "utf-8"
MAX_FILENAME_LEN = 255
