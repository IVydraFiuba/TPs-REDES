import queue
import threading

from lib.archivos.almacenamiento_servidor import AlmacenamientoServidor
from lib.cliente.manejadores import manejador_descarga, manejador_subida
from lib.protocolo_aplicacion import ComunicadorAplicacion
from lib.servidor.sesion import SesionServidor


class CanalMemoria:
    def __init__(self, entrada, salida):
        self._entrada = entrada
        self._salida = salida
        self.cerrado = False

    def enviar(self, datos):
        self._salida.put(datos)

    def recibir(self):
        return self._entrada.get(timeout=1)

    def vaciar(self):
        pass

    def cerrar(self):
        self.cerrado = True


def crear_canales():
    entrada_cliente = queue.Queue()
    entrada_servidor = queue.Queue()
    cliente = CanalMemoria(entrada_cliente, entrada_servidor)
    servidor = CanalMemoria(entrada_servidor, entrada_cliente)
    return cliente, servidor


def iniciar_sesion(canal, almacenamiento):
    errores = []

    def ejecutar():
        try:
            SesionServidor(canal, almacenamiento).ejecutar()
        except Exception as error:
            errores.append(error)

    hilo = threading.Thread(target=ejecutar)
    hilo.start()
    return hilo, errores


def test_subida_completa_entre_manejador_y_sesion(tmp_path):
    origen = tmp_path / "origen.bin"
    contenido = b"\x00\xffcontenido binario" * 200
    origen.write_bytes(contenido)
    almacenamiento = AlmacenamientoServidor(tmp_path / "almacen")
    canal_cliente, canal_servidor = crear_canales()
    hilo, errores = iniciar_sesion(canal_servidor, almacenamiento)

    manejador_subida(
        ComunicadorAplicacion(canal_cliente),
        origen,
        "recibido.bin",
    )
    hilo.join(timeout=1)

    assert not hilo.is_alive()
    assert errores == []
    assert (tmp_path / "almacen" / "recibido.bin").read_bytes() == contenido
    assert canal_servidor.cerrado is True


def test_descarga_completa_entre_manejador_y_sesion(tmp_path):
    almacen = tmp_path / "almacen"
    almacen.mkdir()
    contenido = b"archivo para descargar\x00\xff" * 200
    (almacen / "servidor.bin").write_bytes(contenido)
    almacenamiento = AlmacenamientoServidor(almacen)
    destino = tmp_path / "descargado.bin"
    canal_cliente, canal_servidor = crear_canales()
    hilo, errores = iniciar_sesion(canal_servidor, almacenamiento)

    manejador_descarga(
        ComunicadorAplicacion(canal_cliente),
        destino,
        "servidor.bin",
    )
    hilo.join(timeout=1)

    assert not hilo.is_alive()
    assert errores == []
    assert destino.read_bytes() == contenido
    assert canal_servidor.cerrado is True
