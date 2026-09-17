import sys
import pytest

sys.path.insert(0, "src")

from lib.args import (
    parsear_argumentos_servidor,
    parsear_argumentos_subida,
    parsear_argumentos_descarga,
)


class TestParsearArgumentosServidor:
    def test_argumentos_validos(self):
        args = parsear_argumentos_servidor(
            ["-H", "127.0.0.1", "-p", "8080", "-s", "./storage"]
        )
        assert args.host == "127.0.0.1"
        assert args.port == 8080
        assert args.storage == "./storage"
        assert args.verbose is False
        assert args.quiet is False

    def test_con_verbose(self):
        args = parsear_argumentos_servidor(
            ["-H", "127.0.0.1", "-p", "8080", "-s", "./storage", "-v"]
        )
        assert args.verbose is True
        assert args.quiet is False

    def test_con_quiet(self):
        args = parsear_argumentos_servidor(
            ["-H", "127.0.0.1", "-p", "8080", "-s", "./storage", "-q"]
        )
        assert args.verbose is False
        assert args.quiet is True

    def test_verbose_y_quiet_juntos_falla(self):
        with pytest.raises(SystemExit):
            args = ["-H", "127.0.0.1", "-p", "8080",
                    "-s", "./storage", "-v", "-q"]
            parsear_argumentos_servidor(args)

    def test_falta_host_falla(self):
        with pytest.raises(SystemExit):
            parsear_argumentos_servidor(["-p", "8080", "-s", "./storage"])

    def test_falta_port_falla(self):
        with pytest.raises(SystemExit):
            parsear_argumentos_servidor(
                ["-H", "127.0.0.1", "-s", "./storage"]
            )

    def test_falta_storage_falla(self):
        with pytest.raises(SystemExit):
            parsear_argumentos_servidor(
                ["-H", "127.0.0.1", "-p", "8080"]
            )


class TestParsearArgumentosSubida:
    def test_argumentos_validos(self):
        args = parsear_argumentos_subida(
            ["-H", "127.0.0.1", "-p", "8080", "-s", "./test.txt",
             "-n", "archivo.txt", "-r", "sw"]
        )
        assert args.host == "127.0.0.1"
        assert args.port == 8080
        assert args.src == "./test.txt"
        assert args.name == "archivo.txt"
        assert args.protocol == "sw"
        assert args.verbose is False
        assert args.quiet is False

    def test_con_verbose(self):
        args = parsear_argumentos_subida(
            ["-H", "127.0.0.1", "-p", "8080", "-s", "./test.txt",
             "-n", "archivo.txt", "-r", "sw", "-v"]
        )
        assert args.verbose is True

    def test_con_quiet(self):
        args = parsear_argumentos_subida(
            ["-H", "127.0.0.1", "-p", "8080", "-s", "./test.txt",
             "-n", "archivo.txt", "-r", "sw", "-q"]
        )
        assert args.quiet is True

    def test_verbose_y_quiet_juntos_falla(self):
        with pytest.raises(SystemExit):
            args = ["-H", "127.0.0.1", "-p", "8080", "-s", "./test.txt",
                    "-n", "archivo.txt", "-r", "sw", "-v", "-q"]
            parsear_argumentos_subida(args)

    def test_falta_src_falla(self):
        with pytest.raises(SystemExit):
            parsear_argumentos_subida(
                ["-H", "127.0.0.1", "-p", "8080",
                 "-n", "archivo.txt", "-r", "sw"]
            )

    def test_falta_name_falla(self):
        with pytest.raises(SystemExit):
            parsear_argumentos_subida(
                ["-H", "127.0.0.1", "-p", "8080", "-s", "./test.txt",
                 "-r", "sw"]
            )

    def test_falta_protocol_falla(self):
        with pytest.raises(SystemExit):
            parsear_argumentos_subida(
                ["-H", "127.0.0.1", "-p", "8080", "-s", "./test.txt",
                 "-n", "archivo.txt"]
            )


class TestParsearArgumentosDescarga:
    def test_argumentos_validos(self):
        args = parsear_argumentos_descarga(
            ["-H", "127.0.0.1", "-p", "8080", "-d", "./salida.txt",
             "-n", "archivo.txt", "-r", "sw"]
        )
        assert args.host == "127.0.0.1"
        assert args.port == 8080
        assert args.dst == "./salida.txt"
        assert args.name == "archivo.txt"
        assert args.protocol == "sw"
        assert args.verbose is False
        assert args.quiet is False

    def test_con_verbose(self):
        args = parsear_argumentos_descarga(
            ["-H", "127.0.0.1", "-p", "8080", "-d", "./salida.txt",
             "-n", "archivo.txt", "-r", "sw", "-v"]
        )
        assert args.verbose is True

    def test_con_quiet(self):
        args = parsear_argumentos_descarga(
            ["-H", "127.0.0.1", "-p", "8080", "-d", "./salida.txt",
             "-n", "archivo.txt", "-r", "sw", "-q"]
        )
        assert args.quiet is True

    def test_verbose_y_quiet_juntos_falla(self):
        with pytest.raises(SystemExit):
            args = ["-H", "127.0.0.1", "-p", "8080", "-d", "./salida.txt",
                    "-n", "archivo.txt", "-r", "sw", "-v", "-q"]
            parsear_argumentos_descarga(args)

    def test_falta_dst_falla(self):
        with pytest.raises(SystemExit):
            parsear_argumentos_descarga(
                ["-H", "127.0.0.1", "-p", "8080",
                 "-n", "archivo.txt", "-r", "sw"]
            )

    def test_falta_name_falla(self):
        with pytest.raises(SystemExit):
            parsear_argumentos_descarga(
                ["-H", "127.0.0.1", "-p", "8080", "-d", "./salida.txt",
                 "-r", "sw"]
            )

    def test_falta_protocol_falla(self):
        with pytest.raises(SystemExit):
            parsear_argumentos_descarga(
                ["-H", "127.0.0.1", "-p", "8080", "-d", "./salida.txt",
                 "-n", "archivo.txt"]
            )
