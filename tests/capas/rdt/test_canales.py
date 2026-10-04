import pytest

from lib.constantes import PROTO_DIRECTO, PROTO_SACK, PROTO_SW
from lib.capas.rdt.errores import ErrorModoNoImplementado
from lib.capas.rdt.fabrica import crear_canal, validar_modo
from lib.capas.rdt.implementaciones.directo import CanalDirecto
from lib.capas.rdt.implementaciones.sack import CanalSack
from lib.capas.rdt.implementaciones.stopwait import CanalStopWait

PROTOCOLO_DESCONOCIDO = 99


class EnlaceFalso:
    pass


@pytest.mark.parametrize("protocolo, clase", [
    (PROTO_DIRECTO, CanalDirecto),
    (PROTO_SW, CanalStopWait),
    (PROTO_SACK, CanalSack),
])
def test_fabrica_crea_el_canal_de_cada_protocolo(protocolo, clase):
    canal = crear_canal(protocolo, EnlaceFalso())

    assert isinstance(canal, clase)


@pytest.mark.parametrize(
    "protocolo", [PROTO_DIRECTO, PROTO_SW, PROTO_SACK]
)
def test_validar_modo_acepta_los_protocolos_implementados(protocolo):
    validar_modo(protocolo)


def test_validar_modo_rechaza_un_protocolo_desconocido():
    with pytest.raises(ErrorModoNoImplementado):
        validar_modo(PROTOCOLO_DESCONOCIDO)


def test_fabrica_rechaza_un_protocolo_desconocido():
    with pytest.raises(ErrorModoNoImplementado):
        crear_canal(PROTOCOLO_DESCONOCIDO, EnlaceFalso())
