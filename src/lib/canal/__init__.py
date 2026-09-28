"""Canales de transporte: UDP directo, Stop&Wait, SACK."""

from .canal import Canal
from .factory import crear_canal
from .segmento import (
    ACK,
    DATA,
    FIN,
    MAX_PAYLOAD,
    SYN,
    TAM_CABECERA,
    Segmento,
    desempaquetar,
    empaquetar,
    tipo_nombre,
)

__all__ = [
    "Canal",
    "crear_canal",
    "Segmento",
    "empaquetar",
    "desempaquetar",
    "tipo_nombre",
    "DATA",
    "ACK",
    "SYN",
    "FIN",
    "TAM_CABECERA",
    "MAX_PAYLOAD",
]
