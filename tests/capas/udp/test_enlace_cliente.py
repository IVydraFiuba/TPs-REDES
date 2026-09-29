import socket

import pytest

from lib.capas.udp.cliente import EnlaceClienteUdp
from lib.capas.udp.errores import ErrorTiempoEspera


class SocketConTimeout:
    def __init__(self):
        self.timeout = None

    def setsockopt(self, nivel, opcion, valor):
        pass

    def settimeout(self, timeout):
        self.timeout = timeout

    def recvfrom(self, tamanio):
        raise socket.timeout


def test_permite_definir_un_timeout_por_recepcion():
    conexion = SocketConTimeout()
    enlace = EnlaceClienteUdp(conexion, ("127.0.0.1", 8080))

    with pytest.raises(ErrorTiempoEspera):
        enlace.recibir(timeout=0.01)

    assert 0 < conexion.timeout <= 0.01
