import pytest

from lib.capas.pca import (
    ComunicadorAplicacion,
    ErrorOperacionRemota,
    ErrorRespuesta,
    Mensaje,
    TipoMensaje,
    aceptado,
    codificar_mensaje,
    decodificar_mensaje,
    error_remoto,
)


class CanalFalso:
    def __init__(self, recibidos=()):
        self.enviados = []
        self.recibidos = list(recibidos)
        self.vaciados = 0

    def enviar(self, datos):
        self.enviados.append(datos)

    def recibir(self):
        return self.recibidos.pop(0)

    def vaciar(self):
        self.vaciados += 1


def test_codifica_al_enviar_y_decodifica_al_recibir():
    recibido = Mensaje(TipoMensaje.COMPLETADO)
    canal = CanalFalso([codificar_mensaje(recibido)])
    comunicador = ComunicadorAplicacion(canal)
    enviado = Mensaje(TipoMensaje.FIN_ARCHIVO)

    comunicador.enviar(enviado)

    assert decodificar_mensaje(canal.enviados[0]) == enviado
    assert comunicador.recibir() == recibido


def test_convierte_un_mensaje_de_error_en_excepcion():
    respuesta = error_remoto("ArchivoInexistente", "no existe")
    canal = CanalFalso([codificar_mensaje(respuesta)])
    comunicador = ComunicadorAplicacion(canal)

    with pytest.raises(ErrorOperacionRemota, match="ArchivoInexistente"):
        comunicador.recibir_respuesta()


def test_esperar_valida_tipo_y_ausencia_de_carga():
    respuesta = Mensaje(TipoMensaje.BLOQUE_ARCHIVO, b"datos")
    canal = CanalFalso([codificar_mensaje(respuesta)])
    comunicador = ComunicadorAplicacion(canal)

    with pytest.raises(ErrorRespuesta):
        comunicador.esperar(TipoMensaje.ACEPTADO)


def test_esperar_permite_una_respuesta_con_carga():
    respuesta = aceptado(123)
    canal = CanalFalso([codificar_mensaje(respuesta)])
    comunicador = ComunicadorAplicacion(canal)

    assert comunicador.esperar(
        TipoMensaje.ACEPTADO,
        con_carga=True,
    ) == respuesta


def test_vaciar_delega_en_el_canal():
    canal = CanalFalso()
    comunicador = ComunicadorAplicacion(canal)

    comunicador.vaciar()

    assert canal.vaciados == 1
