import pytest

from lib.archivos.almacenamiento_servidor import AlmacenamientoServidor
from lib.archivos.errores_archivos import (
    ErrorAlmacenamiento,
    ErrorArchivoExistente,
    ErrorArchivoInexistente,
    ErrorNombreArchivo,
    ErrorTransferenciaEnCurso,
)


class TestAlmacenamientoServidor:
    def test_crear_directorio_si_no_existe(self, tmp_path):
        directorio = tmp_path / "nuevo_directorio"
        almacenamiento = AlmacenamientoServidor(directorio)
        assert directorio.is_dir()

    def test_directorio_invalido_lanza_error(self, tmp_path):
        archivo = tmp_path / "archivo.txt"
        archivo.write_bytes(b"no es dir")
        with pytest.raises(ErrorAlmacenamiento):
            AlmacenamientoServidor(archivo)

    def test_directorio_existente_funciona(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)
        assert tmp_path.is_dir()

    def test_abrir_descarga_archivo_existente(self, tmp_path):
        archivo = tmp_path / "test.txt"
        archivo.write_bytes(b"contenido")

        almacenamiento = AlmacenamientoServidor(tmp_path)
        with almacenamiento.abrir_descarga("test.txt") as lector:
            assert lector.leer_bloque(1024) == b"contenido"

    def test_abrir_descarga_archivo_inexistente(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)
        with pytest.raises(ErrorArchivoInexistente):
            almacenamiento.abrir_descarga("no_existe.txt")

    def test_recibir_subida_confirmar(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)

        with almacenamiento.recibir_subida("nuevo.txt") as escritor:
            escritor.escribir_bloque(b"datos")
            escritor.confirmar()

        assert (tmp_path / "nuevo.txt").read_bytes() == b"datos"

    def test_recibir_subida_sin_confirmar_cancela(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)

        with almacenamiento.recibir_subida("nuevo.txt") as escritor:
            escritor.escribir_bloque(b"datos")

        assert not (tmp_path / "nuevo.txt").exists()

    def test_nombre_invalido_punto(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)
        with pytest.raises(ErrorNombreArchivo):
            almacenamiento._ruta(".")

    def test_nombre_invalido_doble_punto(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)
        with pytest.raises(ErrorNombreArchivo):
            almacenamiento._ruta("..")

    def test_nombre_invalido_con_slash(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)
        with pytest.raises(ErrorNombreArchivo):
            almacenamiento._ruta("archivo/../../peligro")

    def test_nombre_invalido_con_backslash(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)
        with pytest.raises(ErrorNombreArchivo):
            almacenamiento._ruta("archivo\\..\\..\\peligro")

    def test_nombre_invalido_null(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)
        with pytest.raises(ErrorNombreArchivo):
            almacenamiento._ruta("archivo\x00peligro")

    def test_nombre_invalido_tmp(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)
        with pytest.raises(ErrorNombreArchivo):
            almacenamiento._ruta("archivo.tmp")

    def test_nombre_invalido_vacio(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)
        with pytest.raises(ErrorNombreArchivo):
            almacenamiento._ruta("")

    def test_subida_archivo_existente_lanza_error(self, tmp_path):
        archivo = tmp_path / "existe.txt"
        archivo.write_bytes(b"ya existe")

        almacenamiento = AlmacenamientoServidor(tmp_path)
        with pytest.raises(ErrorArchivoExistente):
            with almacenamiento.recibir_subida("existe.txt") as escritor:
                pass

    def test_dos_subidas_mismo_nombre_lanza_error(self, tmp_path):
        almacenamiento = AlmacenamientoServidor(tmp_path)

        with almacenamiento.recibir_subida("archivo.txt"):
            with pytest.raises(ErrorTransferenciaEnCurso):
                with almacenamiento.recibir_subida("archivo.txt") as escritor:
                    pass
