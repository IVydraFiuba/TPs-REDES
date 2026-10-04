# Se corre con: sudo python mininet/topologia.py
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
import time

class TopoTP(Topo):
    def build(self):
        # TODO: crear h1 (cliente), h2 (servidor) y un switch.
        # TODO: unirlos con addLink usando cls=TCLink.
        #       El link del cliente lleva la perdida y el retardo:
        #         loss=<porcentaje>       -> 10 para 10%
        #         delay="<ms>ms"          -> OJO: RTT = 2 * delay
        #                                    (RTT 40ms => delay 20ms)
        
        DELAY = '20ms'
        LOSS = 10

        cliente =self.addHost('h1')
        servidor = self.addHost('h2')
        switch_prueba =self.addSwitch('s1',failMode = 'standalone')
        
        self.addLink(cliente,switch_prueba,delay = DELAY,loss = LOSS)
        self.addLink(switch_prueba,servidor)
        
    topo = {'miTopo': (lambda:TopoTP())}

def main():
    
    net = Mininet(topo=TopoTP(), link=TCLink,controller = None)
    net.start()
    
    # TODO: correr el servidor en h2 y el cliente en h1,
    #h1 = net.get("h1")
    #h2 = net.get("h2")

    #h1.cmd("python3 src/lib/cliente/cliente.py &")
    #h2.cmd("python3 src/lib/cliente/cliente.py &")

    #       y medir tiempo / throughput para el analisis.
    
    CLI(net)

    net.stop()


if __name__ == "__main__":
    main()
