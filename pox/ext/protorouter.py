# Import some POX stuff
from pox.core import core                       # Main POX object
import pox.openflow.libopenflow_01 as of        # OpenFlow 1.0 library
from pox.lib.addresses import EthAddr, IPAddr   # Address types
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp

log = core.getLogger()
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"


def log_color(color, msg):
    log.info(f"{color}{msg}{RESET}")


PRIVATE_SUBNET = IPAddr("192.168.1.0")      # Red interna
PRIVATE_MASK = 24                           # Máscara de la red interna
PRIVATE_IP = IPAddr("192.168.1.254")        # IP del router en la red privada
PUBLIC_IP = IPAddr("200.0.0.254")           # IP del router en la red pública
PUBLIC_MAC = EthAddr("00:00:00:aa:aa:aa")   # MAC del router hacia la red pública
PRIVATE_MAC = EthAddr("00:00:00:bb:bb:bb")  # MAC del router hacia la red privada
PUBLIC_PORT = 1                             # Puerto del switch conectado a la red pública

SWITCH_IPS = {
    PRIVATE_IP: PRIVATE_MAC,
    PUBLIC_IP: PUBLIC_MAC,
}


class ProtoRouter(object):
    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)

        self.arp_table = {}       # Diccionario { IPAddr: EthAddr }
        self.packet_buffer = {}     # Diccionario { IPAddr: [lista de eventos pendientes] }

    def _handle_PacketIn(self, event):
        if not event.parsed.parsed:
            log.warning("[DROP] PacketIn con trama no reconocida. POX no pudo decodificar el paquete.")
            return

        if event.parsed.type == ethernet.IP_TYPE:
            self.handle_ip(event)
        elif event.parsed.type == ethernet.ARP_TYPE:
            self.handle_arp(event)
        else:
            log_color(YELLOW, f"Paquete ignorado: protocolo distinto de IPv4.")

    def handle_ip(self, event):
        packet = event.parsed
        ip_pkt = packet.payload
        in_port = event.port

        log_color(
            YELLOW, f"RECIBIDO: {ip_pkt.srcip} → {ip_pkt.dstip} | "
            f"MAC: {packet.src} → {packet.dst} | In Port: {in_port}")

        if ip_pkt.srcip.inNetwork(PRIVATE_SUBNET, PRIVATE_MASK):

            log_color(GREEN, f"MATCH: {ip_pkt.srcip} pertenece a la red privada {PRIVATE_SUBNET}/{PRIVATE_MASK}")

            dest_ip = ip_pkt.dstip  # IP de destino del paquete (ej. el servidor)

            # ¿Conocemos la MAC de destino en nuestra tabla ARP?
            if dest_ip in self.arp_table:
                dest_mac = self.arp_table[dest_ip]
                self.process_ip_with_destination_mac(event, dest_mac)
            else:
                # Si ya hay paquetes esperando esta IP, el request ya salió
                ya_preguntado = dest_ip in self.packet_buffer

                # 1. Guardar el evento en el buffer de pendientes
                self.packet_buffer.setdefault(dest_ip, []).append(event)

                # 2. Emitir ARP Request hacia la red pública (solo la primera vez)
                if ya_preguntado:
                    log_color(YELLOW, f"MAC desconocida para {dest_ip}. Reteniendo paquete (ARP Request ya enviado)")
                else:
                    log_color(YELLOW, f"MAC desconocida para {dest_ip}. Reteniendo paquete y enviando ARP Request...")
                    self.send_arp_request(dest_ip, PUBLIC_PORT)

        else:
            log_color(RED, f"NO MATCH: {ip_pkt.srcip} no pertenece a {PRIVATE_SUBNET}/{PRIVATE_MASK}")

    def handle_arp(self, event):
        # Obtener el paquete ARP
        packet = event.parsed
        arp_pkt = packet.payload

        # Es un request? Preguntan por una IP del switch?
        if arp_pkt.opcode == arp.REQUEST and arp_pkt.protodst in SWITCH_IPS:
            my_mac = SWITCH_IPS[arp_pkt.protodst]

            # El request trae la IP y la MAC de quien pregunta: las aprendemos
            self.arp_table[arp_pkt.protosrc] = arp_pkt.hwsrc
            log_color(GREEN, f"ARP APRENDIDO (request): {arp_pkt.protosrc} está en {arp_pkt.hwsrc}")

            # Paquete ARP de respuesta
            arp_reply = arp()
            arp_reply.opcode = arp.REPLY
            arp_reply.hwsrc = my_mac                  # "mi MAC es esta"
            arp_reply.protosrc = arp_pkt.protodst     # "y soy la IP por la que preguntaste"
            arp_reply.hwdst = arp_pkt.hwsrc           # te contesto a vos (tu MAC)...
            arp_reply.protodst = arp_pkt.protosrc     # ...y a tu IP

            # Armar el reply (arp adentro de ethernet)
            eth = ethernet()
            eth.type = ethernet.ARP_TYPE
            eth.src = my_mac
            eth.dst = arp_pkt.hwsrc
            eth.payload = arp_reply
            # Mandarlo con un packet_out por event.port
            msg = of.ofp_packet_out()
            msg.data = eth.pack()
            msg.actions.append(of.ofp_action_output(port=event.port))
            self.connection.send(msg)
            log_color(GREEN, f"ARP REPLY: {arp_pkt.protodst} is-at {my_mac} → {arp_pkt.protosrc} | Out Port: {event.port}")

        # Es un reply? Guardamos el mapeo IP-MAC en nuestra tabla dinamica
        elif arp_pkt.opcode == arp.REPLY:
            src_ip = arp_pkt.protosrc
            src_mac = arp_pkt.hwsrc

            self.arp_table[src_ip] = src_mac
            log_color(GREEN, f"ARP APRENDIDO: {src_ip} está en {src_mac}")

            # Si teniamos paquetes esperando por esta IP, los despachamos
            if src_ip in self.packet_buffer:
                log_color(CYAN, f"Despachando paquetes pendientes para {src_ip}...")
                for pending_event in self.packet_buffer[src_ip]:
                    self.process_ip_with_destination_mac(pending_event, src_mac)
                del self.packet_buffer[src_ip]

    def send_arp_request(self, target_ip, out_port):
        arp_req = arp()
        arp_req.opcode = arp.REQUEST
        arp_req.hwsrc = PUBLIC_MAC
        arp_req.protosrc = PUBLIC_IP
        arp_req.hwdst = EthAddr("00:00:00:00:00:00")
        arp_req.protodst = target_ip

        eth = ethernet()
        eth.type = ethernet.ARP_TYPE
        eth.src = PUBLIC_MAC
        eth.dst = EthAddr("ff:ff:ff:ff:ff:ff")  # Broadcast
        eth.payload = arp_req

        msg = of.ofp_packet_out()
        msg.data = eth.pack()
        msg.actions.append(of.ofp_action_output(port=out_port))
        self.connection.send(msg)
        log_color(CYAN, f"ARP REQUEST: Who has {target_ip}? Tell {PUBLIC_IP}")

    def process_ip_with_destination_mac(self, event, dest_mac):
        packet = event.parsed
        ip_pkt = packet.payload
        in_port = event.port

        # Instalar Flujo Saliente
        fm = of.ofp_flow_mod()
        fm.idle_timeout = 10

        # Filtro (Saliente)
        fm.match.nw_src = ip_pkt.srcip
        fm.match.dl_type = 0x800  # IPv4
        fm.match.in_port = in_port

        # Acción (Saliente)
        fm.actions.append(of.ofp_action_dl_addr.set_src(PUBLIC_MAC))
        fm.actions.append(of.ofp_action_dl_addr.set_dst(dest_mac))
        fm.actions.append(of.ofp_action_output(port=PUBLIC_PORT))
        self.connection.send(fm)

        # Instalar Flujo Entrante (para respuesta)
        fm_back = of.ofp_flow_mod()
        fm_back.idle_timeout = 10

        # Filtro (Entrante)
        fm_back.match.nw_src = ip_pkt.dstip
        fm_back.match.nw_dst = ip_pkt.srcip
        fm_back.match.dl_type = 0x800  # IPv4
        fm_back.match.in_port = PUBLIC_PORT

        # Acción (Entrante)
        fm_back.actions.append(of.ofp_action_dl_addr.set_src(PRIVATE_MAC))
        fm_back.actions.append(of.ofp_action_dl_addr.set_dst(packet.src))
        fm_back.actions.append(of.ofp_action_output(port=in_port))
        self.connection.send(fm_back)

        # Reenviar paquete actual con MACs actualizadas (Los posteriores pasan por flujo)
        packet.src = PUBLIC_MAC
        packet.dst = dest_mac
        msg = of.ofp_packet_out()
        msg.data = packet.pack()
        msg.actions.append(of.ofp_action_output(port=PUBLIC_PORT))
        log_color(CYAN, f"ENVIANDO: {ip_pkt.srcip} → {ip_pkt.dstip} | MAC: {PUBLIC_MAC} → {dest_mac} | Out Port: {PUBLIC_PORT}")
        self.connection.send(msg)


def launch():

    def start_switch(event):
        log_color(YELLOW, f"Iniciando ProtoRouter para Switch {event.connection.dpid}")
        ProtoRouter(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
