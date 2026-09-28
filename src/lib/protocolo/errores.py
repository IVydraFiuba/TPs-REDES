"""Errores del protocolo de aplicación."""


class ErrorProtocolo(Exception):
    """Error base del protocolo."""


class ErrorMensaje(ErrorProtocolo):
    """El mensaje de aplicación no tiene un formato válido."""


class ErrorComunicacion(ErrorProtocolo):
    """Error en la comunicación UDP."""


class ErrorTiempoEspera(ErrorComunicacion):
    """Tiempo de espera agotado esperando respuesta."""


class ErrorServidorOcupado(ErrorComunicacion):
    """El servidor está atendiendo otra transferencia."""


class ErrorModoNoImplementado(ErrorProtocolo):
    """El modo de protocolo solicitado no está implementado."""


class ErrorOperacionRemota(ErrorProtocolo):
    """El servidor rechazó o interrumpió la transferencia."""


class ErrorRespuesta(ErrorProtocolo):
    """Respuesta inesperada del servidor."""


class ErrorTransferenciaIncompleta(ErrorProtocolo):
    """La cantidad de bytes transferidos no coincide con lo anunciado."""
