"""Errores propios de lectura, escritura y almacenamiento."""


class ErrorArchivo(Exception):
    """Error esperable de una operación de archivos."""


class ErrorArchivoInexistente(ErrorArchivo):
    """El archivo solicitado no existe."""


class ErrorArchivoExistente(ErrorArchivo):
    """Ya hay un archivo definitivo con ese nombre."""


class ErrorTransferenciaEnCurso(ErrorArchivo):
    """El servidor ya está recibiendo un archivo con ese nombre."""


class ErrorNombreArchivo(ErrorArchivo):
    """El nombre no es un nombre de archivo permitido."""


class ErrorTemporalExistente(ErrorArchivo):
    """Ya existe el archivo temporal para ese destino."""


class ErrorLecturaArchivo(ErrorArchivo):
    """No se pudo leer el archivo."""


class ErrorEscrituraArchivo(ErrorArchivo):
    """No se pudo escribir o confirmar el archivo."""


class ErrorEstadoArchivo(ErrorArchivo):
    """Se intentó operar sobre un archivo ya cerrado."""


class ErrorBloqueArchivo(ErrorArchivo):
    """El tamaño o el contenido de un bloque no es válido."""


class ErrorAlmacenamiento(ErrorArchivo):
    """No se pudo preparar el directorio de almacenamiento."""


class ErrorDirectorioDestino(ErrorArchivo):
    """El directorio de destino no es válido o no existe."""
