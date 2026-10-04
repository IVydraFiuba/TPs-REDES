class ErrorSegmento(Exception):
    """Formato de segmento inválido."""

class ErrorModoNoImplementado(Exception):
    """Modo de RDT aún no disponible."""

class ErrorConfirmacion(Exception):
    """Confirmacion de ACK recibido no es el esperado"""
