# lib/transport.py
import logging

from lib.constantes import PROTO_SACK, PROTO_SW
from lib.borrador.sack import SackTransport
from lib.borrador.stopwait import StopWaitTransport

logger = logging.getLogger(__name__)


def crear_transport(protocolo_id, sock, peer_addr):
    if protocolo_id == PROTO_SW:
        return StopWaitTransport(sock, peer_addr)
    if protocolo_id == PROTO_SACK:
        return SackTransport(sock, peer_addr)
    raise ValueError(f"Protocolo desconocido: {protocolo_id}")
