class ErrorMensaje(Exception):
    """Mensaje de aplicación inválido."""


class ErrorRespuesta(ErrorMensaje):
    """Respuesta del peer inesperada."""


class ErrorTransferenciaIncompleta(ErrorMensaje):
    """La cantidad de bytes transferidos no coincide con lo anunciado."""


class ErrorOperacionRemota(ErrorMensaje):
    """El servidor respondió con un error."""
