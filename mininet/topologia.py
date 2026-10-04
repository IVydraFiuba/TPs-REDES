# Topologia de prueba para el TP.
#
#   sudo python3 mininet/topologia.py                 -> abre la CLI
#   sudo python3 mininet/topologia.py --medir         -> corre el analisis
#   sudo python3 mininet/topologia.py --perdida 20 --rtt 300
#
# Se puede correr desde cualquier directorio.
# Si una corrida se corta mal y deja la red montada: sudo mn -c
import argparse
import hashlib
import os
import shutil
import time

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIDOR = os.path.join(RAIZ, "src", "start-server.py")
UPLOAD = os.path.join(RAIZ, "src", "upload.py")
DOWNLOAD = os.path.join(RAIZ, "src", "download.py")

IP_SERVIDOR = "10.0.0.2"
PUERTO = 8080

# Tamanos de la comparacion entre protocolos: el enunciado pide al menos
# tres, y los dos protocolos corren en los tres.
TAMANOS = [("64KB", 64 * 1024),
           ("256KB", 256 * 1024),
           ("1MB", 1024 * 1024)]
# El requisito de tiempo aplica solo a SACK. Stop & Wait con 5 MB tardaria
# mas de una hora, y el enunciado no lo pide.
TAMANO_REQUISITO = ("5MB", 5 * 1024 * 1024)
LIMITE_REQUISITO = 120.0


class TopoTP(Topo):
    """h1 (cliente) --- s1 --- h2 (servidor).

    La perdida y el retardo van en el enlace del cliente. TCLink los
    aplica a las dos interfaces de ese enlace, asi que cada sentido
    cruza una sola interfaz con perdida: la tasa del camino coincide con
    lo configurado. El RTT es el doble del retardo.
    """

    def build(self, perdida=10, retardo_ms=20):
        cliente = self.addHost("h1")
        servidor = self.addHost("h2")
        switch = self.addSwitch("s1", failMode="standalone")

        self.addLink(cliente, switch, cls=TCLink,
                     delay="%dms" % retardo_ms, loss=perdida)
        self.addLink(switch, servidor, cls=TCLink)


# Para poder usarla con: sudo mn --custom mininet/topologia.py --topo tp
topos = {"tp": TopoTP}


def _md5(ruta):
    digest = hashlib.md5()
    with open(ruta, "rb") as archivo:
        for trozo in iter(lambda: archivo.read(1 << 16), b""):
            digest.update(trozo)
    return digest.hexdigest()


def preparar_archivos(directorio):
    """Crea los archivos de prueba que falten."""
    os.makedirs(directorio, exist_ok=True)
    rutas = {}
    for nombre, tam in TAMANOS + [TAMANO_REQUISITO]:
        ruta = os.path.join(directorio, "prueba-%s.bin" % nombre)
        if not os.path.exists(ruta) or os.path.getsize(ruta) != tam:
            with open(ruta, "wb") as archivo:
                archivo.write(os.urandom(tam))
        rutas[nombre] = ruta
    return rutas


def medir(net, perdida, rtt):
    """Sube y baja cada archivo con cada protocolo, y cronometra."""
    h1, h2 = net.get("h1"), net.get("h2")
    trabajo = os.path.join(RAIZ, "mediciones")
    storage = os.path.join(trabajo, "servidor")
    bajadas = os.path.join(trabajo, "bajadas")
    rutas = preparar_archivos(trabajo)

    # Vaciar antes de empezar. Si queda un archivo de una corrida
    # anterior, el servidor rechaza la subida con ErrorArchivoExistente,
    # la transferencia no ocurre, y la verificacion por MD5 igual da bien
    # porque el archivo viejo tiene el contenido correcto: la corrida se
    # anota como "ok" en milisegundos sin haber transferido nada.
    for directorio in (storage, bajadas):
        shutil.rmtree(directorio, ignore_errors=True)
        os.makedirs(directorio, exist_ok=True)
    md5_origen = {n: _md5(r) for n, r in rutas.items()}

    # El log del servidor va a un archivo: si una transferencia falla,
    # es lo unico que cuenta que paso del otro lado.
    ruta_log = os.path.join(trabajo, "servidor.log")
    archivo_log = open(ruta_log, "w")
    servidor = h2.popen(["python3", SERVIDOR, "-H", IP_SERVIDOR,
                         "-p", str(PUERTO), "-s", storage, "-v"],
                        stdout=archivo_log, stderr=archivo_log)
    print("  log del servidor en %s" % ruta_log)
    time.sleep(2)

    filas = []

    def anotar(operacion, protocolo, nombre, tam, tardo, ok, salida):
        filas.append((operacion, protocolo, nombre, perdida, rtt, tardo,
                      tam / 1024.0 / max(tardo, 1e-9), ok))
        print("  %-8s %-6s %-6s %8.2f s %9.1f KB/s  %s"
              % (operacion, protocolo, nombre, tardo,
                 tam / 1024.0 / max(tardo, 1e-9), "ok" if ok else "MAL"))
        if not ok:
            print(salida)

    def correr_par(protocolo, nombre, tam):
        remoto = "%s-%s.bin" % (nombre, protocolo)

        arranque = time.monotonic()
        salida = h1.cmd("python3 %s -H %s -p %d -s %s -n %s -r %s"
                        % (UPLOAD, IP_SERVIDOR, PUERTO, rutas[nombre],
                           remoto, protocolo))
        subida = time.monotonic() - arranque
        subido = os.path.join(storage, remoto)
        ok = os.path.exists(subido) and _md5(subido) == md5_origen[nombre]
        anotar("upload", protocolo, nombre, tam, subida, ok, salida)

        destino = os.path.join(bajadas, remoto)
        arranque = time.monotonic()
        salida = h1.cmd("python3 %s -H %s -p %d -d %s -n %s -r %s"
                        % (DOWNLOAD, IP_SERVIDOR, PUERTO, destino,
                           remoto, protocolo))
        bajada = time.monotonic() - arranque
        ok = os.path.exists(destino) and _md5(destino) == md5_origen[nombre]
        anotar("download", protocolo, nombre, tam, bajada, ok, salida)

        return subida, bajada

    requisito = None
    try:
        print("  -- comparacion Stop & Wait contra SACK --")
        for protocolo in ("sw", "sack"):
            for nombre, tam in TAMANOS:
                correr_par(protocolo, nombre, tam)

        nombre, tam = TAMANO_REQUISITO
        print("  -- requisito: SACK con %s en menos de %d s --"
              % (nombre, LIMITE_REQUISITO))
        requisito = correr_par("sack", nombre, tam)
    finally:
        servidor.terminate()
        archivo_log.close()

    print()
    print("Operacion,Protocolo,Tamano,Perdida %,RTT ms,Tiempo s,"
          "Throughput KB/s,Integro")
    for fila in filas:
        print("%s,%s,%s,%d,%d,%.2f,%.1f,%s"
              % (fila[0], fila[1], fila[2], fila[3], fila[4], fila[5],
                 fila[6], "si" if fila[7] else "no"))

    fallaron = [fila for fila in filas if not fila[7]]
    if fallaron:
        print()
        print("%d de %d transferencias quedaron mal"
              % (len(fallaron), len(filas)))

    if requisito:
        peor = max(requisito)
        print()
        print("Requisito (SACK, %s, %d%% perdida, RTT %d ms): %.2f s "
              "contra un limite de %.0f s -> %s"
              % (TAMANO_REQUISITO[0], perdida, rtt, peor, LIMITE_REQUISITO,
                 "CUMPLE" if peor < LIMITE_REQUISITO else "NO CUMPLE"))


def parsear():
    parser = argparse.ArgumentParser(description="Topologia del TP")
    parser.add_argument("--perdida", type=int, default=10,
                        help="perdida por sentido en %% (default: 10)")
    parser.add_argument("--rtt", type=int, default=40,
                        help="RTT en ms (default: 40)")
    parser.add_argument("--medir", action="store_true",
                        help="corre el analisis en vez de abrir la CLI")
    return parser.parse_args()


def main():
    args = parsear()
    setLogLevel("info")

    net = Mininet(topo=TopoTP(perdida=args.perdida,
                              retardo_ms=args.rtt // 2),
                  link=TCLink, controller=None)
    net.start()
    try:
        if args.medir:
            print("perdida %d%% por sentido, RTT %d ms"
                  % (args.perdida, args.rtt))
            medir(net, args.perdida, args.rtt)
        else:
            print("Servidor:  h2 python3 %s -H %s -p %d -v &"
                  % (SERVIDOR, IP_SERVIDOR, PUERTO))
            print("Cliente:   h1 python3 %s -H %s -p %d "
                  "-s ARCHIVO -n NOMBRE -r sack -v"
                  % (UPLOAD, IP_SERVIDOR, PUERTO))
            CLI(net)
    finally:
        # En un finally: si algo falla antes, la red queda montada y hay
        # que limpiarla a mano con sudo mn -c.
        net.stop()


if __name__ == "__main__":
    main()
