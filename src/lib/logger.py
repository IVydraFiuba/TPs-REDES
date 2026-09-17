# lib/logger.py
import sys
import threading
from datetime import datetime

# Niveles (de menor a mayor verbosidad)
QUIET = 0
NORMAL = 1
VERBOSE = 2


def nivel_desde_flags(verbose, quiet):
    if verbose:
        return VERBOSE
    if quiet:
        return QUIET
    return NORMAL


class Logger:

    def __init__(self, nivel=NORMAL, timestamps=True):
        self.nivel = nivel
        self.timestamps = timestamps
        self._lock = threading.Lock()

    @classmethod
    def desde_args(cls, args, timestamps=True):
        return cls(nivel_desde_flags(args.verbose, args.quiet), timestamps)

    def _emitir(self, texto, stream):
        prefijo = ""
        if self.timestamps:
            prefijo = datetime.now().strftime("[%H:%M:%S] ")
        with self._lock:
            stream.write(f"{prefijo}{texto}\n")
            stream.flush()

    def error(self, texto):
        self._emitir(f"ERROR: {texto}", sys.stderr)

    def info(self, texto):
        if self.nivel >= NORMAL:
            self._emitir(texto, sys.stdout)

    def debug(self, texto):
        if self.nivel >= VERBOSE:
            self._emitir(f"DEBUG: {texto}", sys.stdout)
