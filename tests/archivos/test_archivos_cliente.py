import pytest

from lib.archivos.archivos_cliente import (
    abrir_origen_subida,
    preparar_destino_descarga,
)
from lib.archivos.errores_archivos import (
    ErrorArchivoInexistente,
    ErrorDirectorioDestino,
    ErrorNombreArchivo,
)


class TestAbrirOrigenSubida:
    def test_abrir_archivo_existente(self, tmp_path):
        archivo = tmp_path / "origen.txt"
        archivo.write_bytes(b"contenido")

        with abrir_origen_subida(archivo) as lector:
            assert lector.leer_bloque(1024) == b"contenido"

    def test_abrir_archivo_inexistente(self, tmp_path):
        inexistente = tmp_path / "no_existe.txt"
        with pytest.raises(ErrorArchivoInexistente):
            abrir_origen_subida(inexistente)

    def test_no_permite_temporal(self, tmp_path):
        tmp_file = tmp_path / "archivo.tmp"
        tmp_file.write_bytes(b"temporal")

        with pytest.raises(ErrorNombreArchivo):
            abrir_origen_subida(tmp_file)


class TestPrepararDestinoDescarga:
    def test_preparar_destino_valido(self, tmp_path):
        directorio = tmp_path / "descargas"
        directorio.mkdir()
        destino = directorio / "nuevo.txt"

        with preparar_destino_descarga(destino):
            assert destino.exists() is False

    def test_destino_en_directorio_inexistente(self, tmp_path):
        destino = tmp_path / "no_existe" / "archivo.txt"

        with pytest.raises(ErrorDirectorioDestino):
            preparar_destino_descarga(destino)

    def test_destino_es_directorio(self, tmp_path):
        directorio = tmp_path / "micarpeta"
        directorio.mkdir()

        with pytest.raises(ErrorDirectorioDestino):
            preparar_destino_descarga(directorio)
