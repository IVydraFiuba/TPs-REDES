"""Entrada del controlador: eventos OpenFlow y coordinación del router."""
from pox.core import core
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
from tp_router.ARP import ARP
from tp_router.config import (
    GREEN,
    PRIVATE_MASK,
    PRIVATE_SUBNET,
    PUBLIC_IP,
    RED,
    YELLOW,
    log,
    log_color,
)
from tp_router.flujos import Flujos


class ProtoRouter:
    def __init__(self, connection):
        self.connection = connection
        self.arp = ARP(connection)
        self.flujos = Flujos(connection, self.arp)
        connection.addListeners(self)

    def _handle_PacketIn(self, event):
        if not event.parsed.parsed:
            log.warning("[DROP] PacketIn con trama no reconocida. POX no pudo decodificar el paquete.")
            return

        if event.parsed.type == ethernet.IP_TYPE:
            self.handle_ip(event)
        elif event.parsed.type == ethernet.ARP_TYPE:
            self.arp.handle_arp(event)
        else:
            log_color(YELLOW, f"Paquete ignorado: protocolo distinto de IPv4.")

    def _handle_FlowRemoved(self, event):
        self.flujos.manage_flow_removed(event)


    def handle_ip(self, event):
        packet = event.parsed
        ip_pkt = packet.payload
        in_port = event.port

        log_color(
            YELLOW, f"RECIBIDO: {ip_pkt.srcip} → {ip_pkt.dstip} | "
            f"MAC: {packet.src} → {packet.dst} | In Port: {in_port}")

        if ip_pkt.srcip.inNetwork(PRIVATE_SUBNET, PRIVATE_MASK):

            log_color(GREEN, f"MATCH: {ip_pkt.srcip} pertenece a la red privada {PRIVATE_SUBNET}/{PRIVATE_MASK}")

            dest_ip = ip_pkt.dstip

            dest_mac = self.arp.resolve_mac(event, dest_ip, self.flujos.process_ip_with_destination_mac)
            if dest_mac is None:
                return  # quedó en el buffer
            self.flujos.process_ip_with_destination_mac(event, dest_mac)

        elif ip_pkt.dstip == PUBLIC_IP and ip_pkt.protocol == ipv4.ICMP_PROTOCOL:
            # Respuesta de ping: no tiene regla instalada, la traduce el controlador
            self.flujos.process_icmp_entrante(event)

        else:
            log_color(RED, f"NO MATCH: {ip_pkt.srcip} no pertenece a {PRIVATE_SUBNET}/{PRIVATE_MASK}")



def launch():

    def start_switch(event):
        log_color(YELLOW, f"Iniciando ProtoRouter para Switch {event.connection.dpid}")
        ProtoRouter(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
