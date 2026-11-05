#!/usr/bin/python3

import json
from ipaddress import IPv4Interface
from pathlib import Path
from typing import cast

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.topo import Topo

# Direcciones y conexiones compartidas con el controlador y el diagrama.
CONFIG_PATH = Path(__file__).resolve().with_name("topo_config.json")
with CONFIG_PATH.open() as config_file:
    CONFIG = json.load(config_file)


class NATTopo(Topo):
    def build(self):
        switch = self.addSwitch(CONFIG["switch"])
        for host in CONFIG["hosts"]:
            gateway = IPv4Interface(CONFIG["gateways"][host["network"]]["ip"])
            node = self.addHost(
                host["name"], ip=host["ip"], mac=host["mac"],
                defaultRoute=f"via {gateway.ip}",
            )
            self.addLink(node, switch, port2=host["switch_port"])


def disable_ipv6_hosts(net):
    for host in net.hosts:
        host.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        host.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        host.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")


def disable_ipv6_switch(net):
    switch = cast(OVSSwitch, net.get(CONFIG["switch"]))
    switch.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    switch.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
    switch.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")


def run():
    topo = NATTopo()
    net = Mininet(topo=topo, controller=RemoteController, link=TCLink)
    net.start()

    disable_ipv6_hosts(net)
    disable_ipv6_switch(net)

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
