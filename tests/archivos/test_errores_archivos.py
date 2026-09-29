from lib.archivos.errores_archivos import (
    ErrorAlmacenamiento,
    ErrorArchivo,
    ErrorArchivoExistente,
    ErrorArchivoInexistente,
    ErrorBloqueArchivo,
    ErrorDirectorioDestino,
    ErrorEscrituraArchivo,
    ErrorEstadoArchivo,
    ErrorLecturaArchivo,
    ErrorNombreArchivo,
    ErrorTemporalExistente,
    ErrorTransferenciaEnCurso,
)


class TestErroresArchivos:
    def test_error_archivo_es_excepcion(self):
        assert issubclass(ErrorArchivo, Exception)

    def test_error_archivo_inexistente(self):
        error = ErrorArchivoInexistente("archivo no encontrado")
        assert isinstance(error, ErrorArchivo)
        assert isinstance(error, Exception)

    def test_error_archivo_existente(self):
        error = ErrorArchivoExistente("archivo ya existe")
        assert isinstance(error, ErrorArchivo)

    def test_error_transferencia_en_curso(self):
        error = ErrorTransferenciaEnCurso("transferencia activa")
        assert isinstance(error, ErrorArchivo)

    def test_error_nombre_archivo(self):
        error = ErrorNombreArchivo("nombre inválido")
        assert isinstance(error, ErrorArchivo)

    def test_error_temporal_existente(self):
        error = ErrorTemporalExistente("temporal existe")
        assert isinstance(error, ErrorArchivo)

    def test_error_lectura_archivo(self):
        error = ErrorLecturaArchivo("no se pudo leer")
        assert isinstance(error, ErrorArchivo)

    def test_error_escritura_archivo(self):
        error = ErrorEscrituraArchivo("no se pudo escribir")
        assert isinstance(error, ErrorArchivo)

    def test_error_estado_archivo(self):
        error = ErrorEstadoArchivo("archivo cerrado")
        assert isinstance(error, ErrorArchivo)

    def test_error_bloque_archivo(self):
        error = ErrorBloqueArchivo("bloque inválido")
        assert isinstance(error, ErrorArchivo)

    def test_error_almacenamiento(self):
        error = ErrorAlmacenamiento("directorio no disponible")
        assert isinstance(error, ErrorArchivo)

    def test_error_directorio_destino(self):
        error = ErrorDirectorioDestino("directorio inválido")
        assert isinstance(error, ErrorArchivo)
