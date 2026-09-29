import pytest

from lib.constantes import (
    PROTO_DIRECTO,
    TAMANIO_CABECERA_SEGMENTO,
    TAMANIO_MAX_CARGA_SEGMENTO,
    TAMANIO_MAX_DATAGRAMA,
)
from lib.rdt.errores import ErrorSegmento
from lib.rdt.establecimiento import (
    codificar_syn,
    leer_solicitud_sesion,
    solicitar_sesion,
)
from lib.rdt.segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)


class EnlaceFalso:
    def __init__(self, respuesta):
        self.respuesta = respuesta
        self.enviado = None

    def enviar(self, datos):
        self.enviado = datos

    def recibir(self):
        return self.respuesta


def test_codificar_y_decodificar_segmento_sin_identificador():
    original = Segmento(
        TipoSegmento.DATOS,
        secuencia=7,
        confirmacion=5,
        carga=b"contenido",
    )

    codificado = codificar_segmento(original)

    assert len(codificado) == TAMANIO_CABECERA_SEGMENTO + len(original.carga)
    assert decodificar_segmento(codificado) == original
    assert not hasattr(original, "sesion")


def test_segmento_con_carga_maxima_ocupa_un_datagrama_completo():
    segmento = Segmento(
        TipoSegmento.DATOS,
        carga=b"x" * TAMANIO_MAX_CARGA_SEGMENTO,
    )

    assert len(codificar_segmento(segmento)) == TAMANIO_MAX_DATAGRAMA


@pytest.mark.parametrize("campo", [-1, 0x100000000, True])
def test_rechaza_numeros_de_secuencia_invalidos(campo):
    with pytest.raises(ErrorSegmento):
        codificar_segmento(Segmento(TipoSegmento.DATOS, secuencia=campo))


def test_syn_solo_transporta_el_protocolo():
    segmento = decodificar_segmento(codificar_syn(PROTO_DIRECTO))

    assert segmento.tipo == TipoSegmento.SYN
    assert leer_solicitud_sesion(segmento) == PROTO_DIRECTO


def test_cliente_valida_la_respuesta_del_establecimiento():
    respuesta = codificar_syn(PROTO_DIRECTO)
    enlace = EnlaceFalso(respuesta)

    solicitar_sesion(enlace, PROTO_DIRECTO)

    assert enlace.enviado == codificar_syn(PROTO_DIRECTO)


def test_cliente_rechaza_una_respuesta_de_establecimiento_inesperada():
    respuesta = codificar_segmento(Segmento(TipoSegmento.ACK))
    enlace = EnlaceFalso(respuesta)

    with pytest.raises(ErrorSegmento):
        solicitar_sesion(enlace, PROTO_DIRECTO)
