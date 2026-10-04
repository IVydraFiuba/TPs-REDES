import pytest

from lib.constantes import PROTO_DIRECTO, PROTO_SACK, PROTO_SW
from lib.capas.rdt.errores import ErrorModoNoImplementado
from lib.capas.rdt.fabrica import crear_canal, validar_modo
from lib.capas.rdt.implementaciones.sack import CanalSack
from lib.capas.rdt.implementaciones.stopwait import CanalStopWait


class EnlaceFalso:
    pass


def test_fabrica_crea_el_modo_directo():
    canal = crear_canal(PROTO_DIRECTO, EnlaceFalso())

    assert canal is not None


@pytest.mark.parametrize("protocolo", [PROTO_SW])
def test_fabrica_rechaza_modos_pendientes(protocolo):
    with pytest.raises(ErrorModoNoImplementado):
        validar_modo(protocolo)


def test_modulos_pendientes_se_pueden_importar_sin_habilitarlos():
    with pytest.raises(ErrorModoNoImplementado):
        CanalStopWait(EnlaceFalso())