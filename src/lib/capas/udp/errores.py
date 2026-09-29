class ErrorComunicacion(Exception):
    """No se pudo enviar o recibir un datagrama."""


class ErrorTiempoEspera(ErrorComunicacion):
    """Venció el plazo de recepción."""
