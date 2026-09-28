"""Factory para crear canales de transporte según el protocolo."""

from lib.constantes import PROTO_DIRECTO, PROTO_SACK, PROTO_SW
from lib.protocolo.errores import ErrorModoNoImplementado


def crear_canal(protocolo, conexion, direccion):
    """Crea un canal según el protocolo especificado.

    Args:
        protocolo: constante PROTO_DIRECTO, PROTO_SW o PROTO_SACK
        conexion: socket UDP conectado
        direccion: tupla (host, port) del peer

    Returns:
        Canal: instancia del canal apropiado

    Raises:
        ErrorModoNoImplementado: si el protocolo no está implementado
    """
    if protocolo == PROTO_DIRECTO:
        from .udp_directo import CanalUdpDirecto
        return CanalUdpDirecto(conexion, direccion)

    if protocolo == PROTO_SW:
        from .stopwait import CanalStopWait
        return CanalStopWait(conexion, direccion)

    if protocolo == PROTO_SACK:
        from .sack import CanalSack
        return CanalSack(conexion, direccion)

    raise ErrorModoNoImplementado(
        f"Protocolo {protocolo} no implementado. "
        f"Opciones: PROTO_DIRECTO={PROTO_DIRECTO}, "
        f"PROTO_SW={PROTO_SW}, PROTO_SACK={PROTO_SACK}"
    )
