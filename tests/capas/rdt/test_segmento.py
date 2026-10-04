import pytest

from lib.constantes import (
    MAX_REINTENTOS_SYN,
    PROTO_DIRECTO,
    TAMANIO_CABECERA_SEGMENTO,
    TAMANIO_MAX_CARGA_SEGMENTO,
    TAMANIO_MAX_DATAGRAMA,
)
from lib.capas.rdt.errores import ErrorSegmento
from lib.capas.udp.errores import (
    ErrorComunicacion,
    ErrorTiempoEspera,
)
from lib.capas.rdt.establecimiento import (
    codificar_syn,
    leer_solicitud_sesion,
    solicitar_sesion,
)
from lib.capas.rdt.segmento import (
    Segmento,
    TipoSegmento,
    codificar_segmento,
    decodificar_segmento,
)


class EnlaceFalso:
    """Responde siempre lo mismo; con `vencimientos` simula timeouts."""

    def __init__(self, respuesta, vencimientos=0):
        self.respuesta = respuesta
        self.enviado = None
        self.enviados = []
        self.vencimientos = vencimientos

    def enviar(self, datos):
        self.enviado = datos
        self.enviados.append(datos)

    def recibir(self, timeout=None):
        if self.vencimientos > 0:
            self.vencimientos -= 1
            raise ErrorTiempoEspera("sin respuesta")
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

    # Una respuesta que no es el eco no sirve: se reintenta y, al
    # agotar los intentos, se da la sesion por no establecida.
    with pytest.raises(ErrorComunicacion):
        solicitar_sesion(enlace, PROTO_DIRECTO)

    assert len(enlace.enviados) == MAX_REINTENTOS_SYN


def test_cliente_retransmite_el_syn_si_no_le_contestan():
    respuesta = codificar_syn(PROTO_DIRECTO)
    enlace = EnlaceFalso(respuesta, vencimientos=2)

    solicitar_sesion(enlace, PROTO_DIRECTO)

    # Dos vencimientos y recien al tercer intento llega el eco.
    assert len(enlace.enviados) == 3
    assert all(datos == codificar_syn(PROTO_DIRECTO)
               for datos in enlace.enviados)


def test_cliente_corta_si_el_servidor_nunca_contesta():
    respuesta = codificar_syn(PROTO_DIRECTO)
    enlace = EnlaceFalso(respuesta, vencimientos=MAX_REINTENTOS_SYN)

    with pytest.raises(ErrorComunicacion):
        solicitar_sesion(enlace, PROTO_DIRECTO)
