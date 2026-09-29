"""Implementaciones de canales RDT."""

from .directo import CanalDirecto
from .sack import CanalSack
from .stopwait import CanalStopWait

__all__ = ["CanalDirecto", "CanalSack", "CanalStopWait"]
