"""Reglas de forwarding actuales y envío del primer paquete (sin PAT)."""
import pox.openflow.libopenflow_01 as of

from .config import CYAN, PRIVATE_MAC, PUBLIC_MAC, PUBLIC_PORT, log_color


class Flujos:
    def __init__(self, connection):
        self.connection = connection

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

