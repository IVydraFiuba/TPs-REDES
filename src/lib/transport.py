# lib/transport.py
from lib.constants import PROTO_SW, PROTO_SACK
from lib.stopwait import StopWaitTransport
from lib.sack import SackTransport


def crear_transport(protocolo_id, sock, peer_addr, logger):
    if protocolo_id == PROTO_SW:
        return StopWaitTransport(sock, peer_addr, logger)
    if protocolo_id == PROTO_SACK:
        return SackTransport(sock, peer_addr, logger)
    raise ValueError(f"Protocolo desconocido: {protocolo_id}")
