import threading

from lib.constantes import PROTO_DIRECTO
from lib.rdt.establecimiento import codificar_syn
from lib.rdt.segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
)
from lib.servidor.despachador import Despachador
from lib.servidor.registro_sesiones import (
    EntradaSesion,
    RegistroSesiones,
)
from lib.udp.sesion import EnlaceSesionUdp


class SocketFalso:
    def __init__(self):
        self.enviados = []

    def sendto(self, datos, direccion):
        self.enviados.append((datos, direccion))


def crear_entrada(conexion, direccion, respuesta=b"syn"):
    enlace = EnlaceSesionUdp(conexion, direccion, capacidad=2)
    return EntradaSesion(PROTO_DIRECTO, enlace, respuesta)


def test_registro_no_reemplaza_sesiones_y_respeta_el_limite():
    conexion = SocketFalso()
    primera = ("127.0.0.1", 9001)
    segunda = ("127.0.0.1", 9002)
    registro = RegistroSesiones(maximo=1)
    entrada = crear_entrada(conexion, primera)

    assert registro.agregar(primera, entrada) is True
    assert registro.agregar(primera, entrada) is False
    assert registro.agregar(
        segunda, crear_entrada(conexion, segunda)
    ) is False
    assert registro.buscar(primera) is entrada
    assert registro.quitar(primera) is entrada
    assert registro.buscar(primera) is None


def test_despachador_entrega_por_endpoint():
    conexion = SocketFalso()
    direccion = ("127.0.0.1", 9001)
    despachador = Despachador(conexion, None, threading.Event())
    entrada = crear_entrada(conexion, direccion)
    despachador._registro.agregar(direccion, entrada)
    datos = codificar_segmento(
        Segmento(TipoSegmento.DATOS, carga=b"mensaje")
    )

    despachador._distribuir(datos, direccion)

    assert entrada.enlace.recibir() == datos


def test_syn_duplicado_reenvia_la_respuesta_existente():
    conexion = SocketFalso()
    direccion = ("127.0.0.1", 9001)
    respuesta = codificar_syn(PROTO_DIRECTO)
    despachador = Despachador(conexion, None, threading.Event())
    entrada = crear_entrada(conexion, direccion, respuesta)
    despachador._registro.agregar(direccion, entrada)

    despachador._distribuir(codificar_syn(PROTO_DIRECTO), direccion)

    assert conexion.enviados == [(respuesta, direccion)]


def test_datagrama_de_endpoint_desconocido_se_descarta():
    conexion = SocketFalso()
    despachador = Despachador(conexion, None, threading.Event())
    datos = codificar_segmento(Segmento(TipoSegmento.DATOS))

    despachador._distribuir(datos, ("127.0.0.1", 9001))

    assert conexion.enviados == []


def test_fin_de_sesion_elimina_el_endpoint_del_registro():
    class SesionFalsa:
        def ejecutar(self):
            pass

    conexion = SocketFalso()
    direccion = ("127.0.0.1", 9001)
    despachador = Despachador(conexion, None, threading.Event())
    entrada = crear_entrada(conexion, direccion)
    despachador._registro.agregar(direccion, entrada)

    despachador._ejecutar_sesion(direccion, entrada, SesionFalsa())

    assert despachador._registro.buscar(direccion) is None
    assert entrada.enlace.entregar(b"tardio") is False
