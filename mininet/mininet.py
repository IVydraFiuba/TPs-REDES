# Se corre con: sudo python mininet/topologia.py

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI


class TopoTP(Topo):
    def build(self):
        # TODO: crear h1 (cliente), h2 (servidor) y un switch.
        # TODO: unirlos con addLink usando cls=TCLink.
        #       El link del cliente lleva la perdida y el retardo:
        #         loss=<porcentaje>       -> 10 para 10%
        #         delay="<ms>ms"          -> OJO: RTT = 2 * delay
        #                                    (RTT 40ms => delay 20ms)
        pass


def main():
    net = Mininet(topo=TopoTP(), link=TCLink)
    net.start()

    # TODO: correr el servidor en h2 y el cliente en h1,
    #       y medir tiempo / throughput para el analisis.
    CLI(net)

    net.stop()


if __name__ == "__main__":
    main()