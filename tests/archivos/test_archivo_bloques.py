import pytest

from lib.archivos.archivo_bloques import EscritorArchivo, LectorArchivo
from lib.archivos.errores_archivos import (
    ErrorArchivoExistente,
    ErrorArchivoInexistente,
    ErrorBloqueArchivo,
    ErrorEscrituraArchivo,
    ErrorEstadoArchivo,
    ErrorLecturaArchivo,
    ErrorTemporalExistente,
)


class TestLectorArchivo:
    def test_leer_archivo_existente(self, tmp_path):
        archivo = tmp_path / "test.txt"
        archivo.write_bytes(b"hola mundo")

        with LectorArchivo(archivo) as lector:
            contenido = lector.leer_bloque(1024)
            assert contenido == b"hola mundo"

    def test_leer_en_bloques(self, tmp_path):
        archivo = tmp_path / "test.txt"
        archivo.write_bytes(b"abcdefghij")

        with LectorArchivo(archivo) as lector:
            bloque1 = lector.leer_bloque(4)
            bloque2 = lector.leer_bloque(4)
            bloque3 = lector.leer_bloque(4)
            assert bloque1 == b"abcd"
            assert bloque2 == b"efgh"
            assert bloque3 == b"ij"

    def test_leer_bloque_vacio_al_final(self, tmp_path):
        archivo = tmp_path / "test.txt"
        archivo.write_bytes(b"ab")

        with LectorArchivo(archivo) as lector:
            lector.leer_bloque(2)
            final = lector.leer_bloque(1024)
            assert final == b""

    def test_leer_bloque_tamano_invalido(self, tmp_path):
        archivo = tmp_path / "test.txt"
        archivo.write_bytes(b"hola")

        with LectorArchivo(archivo) as lector:
            with pytest.raises(ErrorBloqueArchivo):
                lector.leer_bloque(0)
            with pytest.raises(ErrorBloqueArchivo):
                lector.leer_bloque(-1)
            with pytest.raises(ErrorBloqueArchivo):
                lector.leer_bloque("abc")

    def test_leer_archivo_inexistente(self, tmp_path):
        inexistente = tmp_path / "no_existe.txt"
        with pytest.raises(ErrorArchivoInexistente):
            LectorArchivo(inexistente)

    def test_leer_dos_errores_separados(self, tmp_path):
        archivo = tmp_path / "test.txt"
        with pytest.raises(ErrorArchivoInexistente):
            LectorArchivo(archivo)
        with pytest.raises(ErrorArchivoInexistente):
            LectorArchivo(archivo)


class TestEscritorArchivo:
    def test_escribir_y_confirmar(self, tmp_path):
        archivo = tmp_path / "test.txt"

        with EscritorArchivo(archivo) as escritor:
            escritor.escribir_bloque(b"hola ")
            escritor.escribir_bloque(b"mundo")
            escritor.confirmar()

        assert archivo.read_bytes() == b"hola mundo"

    def test_escribir_en_bloques(self, tmp_path):
        archivo = tmp_path / "test.txt"

        with EscritorArchivo(archivo) as escritor:
            escritor.escribir_bloque(b"abcd")
            escritor.escribir_bloque(b"efgh")
            escritor.confirmar()

        assert archivo.read_bytes() == b"abcdefgh"

    def test_cancelar_elimina_temporal(self, tmp_path):
        archivo = tmp_path / "test.txt"

        with EscritorArchivo(archivo) as escritor:
            escritor.escribir_bloque(b"datos")

        assert not archivo.exists()
        assert not archivo.with_name(archivo.name + ".tmp").exists()

    def test_context_manager_cancela_si_no_confirma(self, tmp_path):
        archivo = tmp_path / "test.txt"

        with pytest.raises(Exception):
            with EscritorArchivo(archivo) as escritor:
                escritor.escribir_bloque(b"datos")
                raise ValueError("error simulado")

        assert not archivo.exists()

    def test_archivo_existente_lanza_error(self, tmp_path):
        archivo = tmp_path / "test.txt"
        archivo.write_bytes(b"existe")

        with pytest.raises(ErrorArchivoExistente):
            EscritorArchivo(archivo)

    def test_confirmar_si_ya_existe_lanza_error(self, tmp_path):
        archivo = tmp_path / "test.txt"
        archivo.write_bytes(b"original")

        tmp_file = archivo.with_name(archivo.name + ".tmp")
        tmp_file.write_bytes(b"temporal")

        with pytest.raises(ErrorArchivoExistente):
            EscritorArchivo(archivo)

    def test_escribir_bloque_no_bytes_lanza_error(self, tmp_path):
        archivo = tmp_path / "test.txt"

        with EscritorArchivo(archivo) as escritor:
            with pytest.raises(ErrorBloqueArchivo):
                escritor.escribir_bloque("string")
            with pytest.raises(ErrorBloqueArchivo):
                escritor.escribir_bloque(123)

    def test_escribir_despues_de_confirmar_lanza_error(self, tmp_path):
        archivo = tmp_path / "test.txt"

        with EscritorArchivo(archivo) as escritor:
            escritor.escribir_bloque(b"hola")
            escritor.confirmar()
            with pytest.raises(ErrorEstadoArchivo):
                escritor.escribir_bloque(b"mas")

    def test_confirmar_dos_veces_lanza_error(self, tmp_path):
        archivo = tmp_path / "test.txt"

        with EscritorArchivo(archivo) as escritor:
            escritor.escribir_bloque(b"hola")
            escritor.confirmar()
            with pytest.raises(ErrorEstadoArchivo):
                escritor.confirmar()

    def test_cancelar_dos_veces_no_falla(self, tmp_path):
        archivo = tmp_path / "test.txt"

        escritor = EscritorArchivo(archivo)
        escritor.escribir_bloque(b"hola")
        escritor.cancelar()
        escritor.cancelar()
        assert not archivo.exists()
