"""Resolución ARP y retención de paquetes pendientes."""
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import EthAddr
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import ethernet

from .config import (
    CYAN,
    GREEN,
    PUBLIC_IP,
    PUBLIC_MAC,
    PUBLIC_PORT,
    SWITCH_IPS,
    YELLOW,
    log_color,
)


class ARP:
    def __init__(self, connection, on_resolved):
        self.connection = connection
        self.on_resolved = on_resolved
        self.arp_table = {}  # IPAddr -> EthAddr
        self.packet_buffer = {}  # IPAddr -> eventos pendientes

    def handle_arp(self, event):
        packet = event.parsed
        arp_pkt = packet.payload

        if arp_pkt.opcode == arp.REQUEST and arp_pkt.protodst in SWITCH_IPS:
            my_mac = SWITCH_IPS[arp_pkt.protodst]

            # Quien pregunta nos deja su IP y MAC
            self.arp_table[arp_pkt.protosrc] = arp_pkt.hwsrc
            log_color(GREEN, f"ARP APRENDIDO (request): {arp_pkt.protosrc} está en {arp_pkt.hwsrc}")

            # Paquete ARP de respuesta
            arp_reply = arp()
            arp_reply.opcode = arp.REPLY
            # Origen: IP por la que preguntaron y su MAC
            arp_reply.protosrc = arp_pkt.protodst
            arp_reply.hwsrc = my_mac
            # Destino: quien preguntó
            arp_reply.protodst = arp_pkt.protosrc
            arp_reply.hwdst = arp_pkt.hwsrc

            eth = ethernet()
            eth.type = ethernet.ARP_TYPE
            eth.src = my_mac
            eth.dst = arp_pkt.hwsrc
            eth.payload = arp_reply

            # Vuelve por el mismo puerto por donde llegó el request
            msg = of.ofp_packet_out()
            msg.data = eth.pack()
            msg.actions.append(of.ofp_action_output(port=event.port))
            self.connection.send(msg)
            log_color(GREEN, f"ARP REPLY: {arp_pkt.protodst} is-at {my_mac} → {arp_pkt.protosrc} | Out Port: {event.port}")

        elif arp_pkt.opcode == arp.REPLY:
            src_ip = arp_pkt.protosrc
            src_mac = arp_pkt.hwsrc

            self.arp_table[src_ip] = src_mac
            log_color(GREEN, f"ARP APRENDIDO: {src_ip} está en {src_mac}")

            # Si teniamos paquetes esperando por esta IP, los enviamos
            if src_ip in self.packet_buffer:
                log_color(CYAN, f"Despachando paquetes pendientes para {src_ip}...")
                for pending_event in self.packet_buffer[src_ip]:
                    self.on_resolved(pending_event, src_mac)
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
        eth.dst = EthAddr("ff:ff:ff:ff:ff:ff")
        eth.payload = arp_req

        msg = of.ofp_packet_out()
        msg.data = eth.pack()
        msg.actions.append(of.ofp_action_output(port=out_port))
        self.connection.send(msg)
        log_color(CYAN, f"ARP REQUEST: Who has {target_ip}? Tell {PUBLIC_IP}")


    def resolve_mac(self, event, ip):
        """Punto de entrada de ARP.

        Devuelve la MAC de ip si está en la tabla ARP.
        Si no, retiene event en el buffer, manda un ARP request (solo el
        primero por IP) y devuelve None. Cuando llega el reply, handle_arp
        invoca on_resolved(event, mac) por cada evento
        retenido.
        """

        if ip in self.arp_table:
            return self.arp_table[ip]

        already_asked = ip in self.packet_buffer
        self.packet_buffer.setdefault(ip, []).append(event)

        if already_asked:
            log_color(YELLOW, f"MAC desconocida para {ip}. Reteniendo paquete (ARP Request ya enviado)")
        else:
            log_color(YELLOW, f"MAC desconocida para {ip}. Reteniendo paquete y enviando ARP Request...")
            self.send_arp_request(ip, PUBLIC_PORT)
        return None


