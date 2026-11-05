"""Configuración del router y logs compartidos.

Mapeo de topo_config.json con la topología actual (valores de ejemplo):

    h1 (200.0.0.1/24) -------- puerto 1 de s1 [lado público]
    h2 (192.168.1.2/24) ------ puerto 2 de s1 [lado privado]
    h3 (192.168.1.3/24) ------ puerto 3 de s1 [lado privado]
    h4 (192.168.1.4/24) ------ puerto 4 de s1 [lado privado]

    gateways.public  -> 200.0.0.254/24, MAC 00:00:00:aa:aa:aa
    gateways.private -> 192.168.1.254/24, MAC 00:00:00:bb:bb:bb

Los gateways son las identidades lógicas del router en cada red, no hosts
adicionales. 

Para cambiar direcciones o conexiones, editar el JSON; estos
comentarios solo ilustran la configuración inicial.
"""
import json
from ipaddress import IPv4Interface
from pathlib import Path

from pox.core import core
from pox.lib.addresses import EthAddr, IPAddr

# buscamos el archivo topo_config.json con la configuracion de la topologia 
CONFIG_PATH = Path(__file__).resolve().parents[3] / "topo_config.json"
with CONFIG_PATH.open() as config_file:
    TOPO_CONFIG = json.load(config_file)

# Cada entrada de gateways contiene una IP con prefijo y una MAC como texto. (lo pueden ver en topo_config.json)
_private = TOPO_CONFIG["gateways"]["private"]
_public = TOPO_CONFIG["gateways"]["public"]

# IPv4Interface separa la IP del gateway de la red y del prefijo:
# "192.168.1.254/24" -> IP 192.168.1.254, red 192.168.1.0, prefijo 24.
_private_interface = IPv4Interface(_private["ip"])
PRIVATE_SUBNET = IPAddr(str(_private_interface.network.network_address))
PRIVATE_MASK = _private_interface.network.prefixlen


# PRIVATE_IP es el gateway de h2/h3/h4; 
# PUBLIC_IP es el gateway de h1.
PRIVATE_IP = IPAddr(str(_private_interface.ip))
PRIVATE_MAC = EthAddr(_private["mac"])

PUBLIC_IP = IPAddr(str(IPv4Interface(_public["ip"]).ip))
PUBLIC_MAC = EthAddr(_public["mac"])

# importante: IPAddr y EthAddr son los tipos que POX utiliza al construir paquetes y reglas.


# IP del router -> MAC con la que responde a consultas ARP por esa IP.
SWITCH_IPS = {
    PRIVATE_IP: PRIVATE_MAC,
    PUBLIC_IP: PUBLIC_MAC,
}
# importante: No es la caché ARP de los hosts --> sus MAC se aprenden dicamicamente en ARP.py


# La topología tiene un único host público (actualmente h1, en el puerto 1 de s1).
# next() obtiene ese host; asumimos que el JSON mantiene un solo host público.
_public_host = next(
    host for host in TOPO_CONFIG["hosts"] if host["network"] == "public"
)
PUBLIC_PORT = _public_host["switch_port"]
# importante: PUBLIC_PORT es un puerto del switch, no un puerto TCP/UDP.

# Segundos sin ver un ARP de una IP tras los cuales su entrada en la tabla ARP
# se considera vieja y se vuelve a resolver (evita usar MACs desactualizadas).
ARP_TIMEOUT = 20



# Logger de POX y colores ANSI para distinguir mensajes en la terminal.
log = core.getLogger()
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"


def log_color(color, msg):
    # RESET evita que el color se aplique también a los mensajes siguientes.
    log.info(f"{color}{msg}{RESET}")