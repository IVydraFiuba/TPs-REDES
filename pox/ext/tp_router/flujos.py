"""Reglas de forwarding con traducción PAT y envío del primer paquete."""
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ipv4 import ipv4

from .config import CYAN, PRIVATE_MAC, PUBLIC_MAC, PUBLIC_PORT, log_color, PUBLIC_IP
from .PAT import PAT


class Flujos:
    def __init__(self, connection):
        self.connection = connection
        self.pat = PAT()

    def manage_flow_removed(self, event):
        match = event.ofp.match
        if(match.in_port == PUBLIC_PORT):
            #Vencio la regla entrante
            self.pat.regla_vencida(match.nw_proto, match.tp_dst, "entrante")
        else:
            #Vencio la regla saliente
            out_port = self.pat.salientes.get((match.nw_proto, match.nw_src, match.tp_src))
            self.pat.regla_vencida(match.nw_proto, out_port, "saliente")
    

    def process_ip_with_destination_mac(self, event, dest_mac):
        packet = event.parsed
        ip_pkt = packet.payload
        trans_pkt = ip_pkt.payload
        in_port = event.port

        #Por si es ICMP, así no rompe, pero no funciona el ping
        if(ip_pkt.protocol != ipv4.TCP_PROTOCOL and ip_pkt.protocol != ipv4.UDP_PROTOCOL):
            return

        out_port = self.pat.obtener_puerto(ip_pkt.protocol, ip_pkt.srcip, trans_pkt.srcport)

        if(out_port is None):
            return

        # Instalar Flujo Saliente
        fm = of.ofp_flow_mod()
        fm.idle_timeout = 10
        fm.flags = of.OFPFF_SEND_FLOW_REM #Flag para cuando venza la regla

        # Filtro (Saliente)
        fm.match.nw_src = ip_pkt.srcip
        fm.match.dl_type = 0x800  # IPv4
        fm.match.in_port = in_port

        fm.match.nw_proto = ip_pkt.protocol    # TCP o UDP
        fm.match.nw_dst = ip_pkt.dstip         # IP destino
        fm.match.tp_src = trans_pkt.srcport    # puerto origen
        fm.match.tp_dst = trans_pkt.dstport    # puerto destino

        # Acción (Saliente)
        fm.actions.append(of.ofp_action_dl_addr.set_src(PUBLIC_MAC))
        fm.actions.append(of.ofp_action_dl_addr.set_dst(dest_mac))        
        fm.actions.append(of.ofp_action_nw_addr.set_src(PUBLIC_IP))
        fm.actions.append(of.ofp_action_tp_port.set_src(out_port))
        fm.actions.append(of.ofp_action_output(port=PUBLIC_PORT))
        self.connection.send(fm)

        # Instalar Flujo Entrante (para respuesta)
        fm_back = of.ofp_flow_mod()
        fm_back.idle_timeout = 10
        fm_back.flags = of.OFPFF_SEND_FLOW_REM #Flag para cuando venza la regla
        
        # Filtro (Entrante)
        fm_back.match.nw_src = ip_pkt.dstip
        fm_back.match.nw_dst = PUBLIC_IP 
        fm_back.match.dl_type = 0x800  # IPv4
        fm_back.match.in_port = PUBLIC_PORT

        fm_back.match.nw_proto = ip_pkt.protocol                
        fm_back.match.tp_src = trans_pkt.dstport
        fm_back.match.tp_dst = out_port

        # Acción (Entrante)
        fm_back.actions.append(of.ofp_action_dl_addr.set_src(PRIVATE_MAC))
        fm_back.actions.append(of.ofp_action_dl_addr.set_dst(packet.src))
        # reescribo IP y puerto de destino a los privados
        fm_back.actions.append(of.ofp_action_nw_addr.set_dst(ip_pkt.srcip))
        fm_back.actions.append(of.ofp_action_tp_port.set_dst(trans_pkt.srcport))
        fm_back.actions.append(of.ofp_action_output(port=in_port))
        self.connection.send(fm_back)

        # Reenviar paquete actual con MACs actualizadas (Los posteriores pasan por flujo)
        packet.src = PUBLIC_MAC
        packet.dst = dest_mac
        ip_pkt.srcip = PUBLIC_IP
        trans_pkt.srcport = out_port        
        msg = of.ofp_packet_out()
        msg.data = packet.pack()
        msg.actions.append(of.ofp_action_output(port=PUBLIC_PORT))
        log_color(CYAN, f"ENVIANDO: {ip_pkt.srcip} → {ip_pkt.dstip} | MAC: {PUBLIC_MAC} → {dest_mac} | Out Port: {PUBLIC_PORT}")
        self.connection.send(msg)

