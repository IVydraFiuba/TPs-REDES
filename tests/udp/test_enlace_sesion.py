import pytest

from lib.udp.errores import ErrorComunicacion
from lib.udp.sesion import EnlaceSesionUdp


class SocketFalso:
    def __init__(self):
        self.enviados = []

    def sendto(self, datos, direccion):
        self.enviados.append((datos, direccion))


def test_entrega_y_recibe_desde_la_cola():
    enlace = EnlaceSesionUdp(
        SocketFalso(), ("127.0.0.1", 9000), capacidad=1
    )

    assert enlace.entregar(b"datagrama") is True
    assert enlace.recibir() == b"datagrama"


def test_informa_cola_llena_sin_bloquear():
    enlace = EnlaceSesionUdp(
        SocketFalso(), ("127.0.0.1", 9000), capacidad=1
    )

    assert enlace.entregar(b"primero") is True
    assert enlace.entregar(b"segundo") is False


def test_envia_al_endpoint_asociado():
    conexion = SocketFalso()
    direccion = ("127.0.0.1", 9000)
    enlace = EnlaceSesionUdp(conexion, direccion, capacidad=1)

    enlace.enviar(b"respuesta")

    assert conexion.enviados == [(b"respuesta", direccion)]


def test_interrumpir_impide_recibir_enviar_y_entregar():
    enlace = EnlaceSesionUdp(
        SocketFalso(), ("127.0.0.1", 9000), capacidad=1
    )

    enlace.interrumpir()

    assert enlace.entregar(b"datagrama") is False
    with pytest.raises(ErrorComunicacion):
        enlace.enviar(b"datagrama")
    with pytest.raises(ErrorComunicacion):
        enlace.recibir()
