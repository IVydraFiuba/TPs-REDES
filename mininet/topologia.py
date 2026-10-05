# Topologia de prueba para el TP.
#
#   sudo python3 mininet/topologia.py                 -> abre la CLI
#   sudo python3 mininet/topologia.py --medir         -> corre el analisis
#   sudo python3 mininet/topologia.py --concurrencia  -> 4 clientes
#   sudo python3 mininet/topologia.py --perdida 20 --rtt 300
#
# Se puede correr desde cualquier directorio.
# Si una corrida se corta mal y deja la red montada: sudo mn -c
import argparse
import hashlib
import os
import shutil
import tempfile
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

# Prueba de concurrencia: dos subidas y dos bajadas a la vez, cada
# una desde un host distinto. h2 es el servidor, asi que los
# clientes son h1, h3, h4 y h5.
TAMANO_CONCURRENCIA = "1MB"
CLIENTES = ("h1", "h3", "h4", "h5")


class TopoTP(Topo):
    """h1, h3, h4, h5 (clientes) --- s1 --- h2 (servidor).

    La perdida y el retardo van en los enlaces de los clientes. TCLink
    los aplica a las dos interfaces de cada enlace, asi que cada sentido
    cruza una sola interfaz con perdida: la tasa del camino coincide con
    lo configurado. El RTT es el doble del retardo.

    Las IP se fijan a mano para no depender del orden en que mininet las
    reparte: h2 tiene que seguir siendo IP_SERVIDOR.

    Los clientes de mas existen para la prueba de concurrencia. En las
    corridas normales quedan ociosos y no molestan: solo se usa h1.
    """

    def build(self, perdida=10, retardo_ms=20):
        switch = self.addSwitch("s1", failMode="standalone")
        servidor = self.addHost("h2", ip="10.0.0.2/8")
        self.addLink(switch, servidor, cls=TCLink)

        for nombre in CLIENTES:
            cliente = self.addHost(nombre, ip="10.0.0.%s/8" % nombre[1:])
            self.addLink(cliente, switch, cls=TCLink,
                         delay="%dms" % retardo_ms, loss=perdida)


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


def _preparar_directorios(trabajo):
    """Vacia storage y bajadas, y devuelve sus rutas.

    Si queda un archivo de una corrida anterior, el servidor rechaza la
    subida con ErrorArchivoExistente, la transferencia no ocurre, y la
    verificacion por MD5 igual da bien porque el archivo viejo tiene el
    contenido correcto: la corrida se anota como "ok" en milisegundos
    sin haber transferido nada.
    """
    storage = os.path.join(trabajo, "servidor")
    bajadas = os.path.join(trabajo, "bajadas")
    for directorio in (storage, bajadas):
        shutil.rmtree(directorio, ignore_errors=True)
        os.makedirs(directorio, exist_ok=True)
    return storage, bajadas


def _arrancar_servidor(h2, trabajo, storage, verboso=True):
    """Levanta el servidor; devuelve (proceso, archivo de log, rutas).

    El log se escribe en /tmp y se copia al final. mediciones/ vive en
    /mnt/c, y ahi cada linea cruza 9p: con -v son mas de cien mil lineas
    y ese costo se mete en los tiempos que estamos midiendo. Se notaba
    como una asimetria falsa, porque el servidor loguea mucho mas cuando
    envia que cuando recibe: las bajadas salian 2.4x mas lentas que las
    subidas por el log, no por el protocolo.
    """
    rutas_log = (os.path.join(tempfile.gettempdir(), "servidor-tp.log"),
                 os.path.join(trabajo, "servidor.log"))
    archivo_log = open(rutas_log[0], "w")
    comando = ["python3", SERVIDOR, "-H", IP_SERVIDOR,
               "-p", str(PUERTO), "-s", storage]
    # Con -v el servidor escribe ~20 lineas por segmento. Sirve para
    # diagnosticar, pero es trabajo que compite con la transferencia:
    # --silencioso lo apaga para medir sin esa interferencia.
    comando.append("-v" if verboso else "-q")
    proceso = h2.popen(comando, stdout=archivo_log, stderr=archivo_log)
    print("  log del servidor en %s (se copia a %s al terminar)%s"
          % (rutas_log + ("" if verboso else "  [silencioso]",)))
    time.sleep(2)
    return proceso, archivo_log, rutas_log


def concurrencia(net, protocolo, verboso=True):
    """Corre dos subidas y dos bajadas en paralelo, una por host.

    Es la prueba que pide la demo. Lo que demuestra es que el servidor
    atiende varias sesiones a la vez: el despachador reparte por
    endpoint y levanta un hilo por sesion. Que el tiempo total sea menor
    que la suma de los individuales es la evidencia del solapamiento.
    """
    trabajo = os.path.join(RAIZ, "mediciones")
    rutas = preparar_archivos(trabajo)
    storage, bajadas = _preparar_directorios(trabajo)
    origen = rutas[TAMANO_CONCURRENCIA]
    md5_origen = _md5(origen)

    tareas = [(CLIENTES[0], "upload", "concurrente-a.bin"),
              (CLIENTES[1], "upload", "concurrente-b.bin"),
              (CLIENTES[2], "download", "concurrente-c.bin"),
              (CLIENTES[3], "download", "concurrente-d.bin")]

    # Las bajadas necesitan el archivo ya publicado en el servidor.
    for _, operacion, remoto in tareas:
        if operacion == "download":
            shutil.copyfile(origen, os.path.join(storage, remoto))

    servidor, archivo_log, rutas_log = _arrancar_servidor(
        net.get("h2"), trabajo, storage, verboso
    )
    print("  %d clientes en paralelo, %s de %s cada uno"
          % (len(tareas), TAMANO_CONCURRENCIA, protocolo))

    lanzados = []
    try:
        arranque = time.monotonic()
        for host, operacion, remoto in tareas:
            if operacion == "upload":
                comando = ["python3", UPLOAD, "-s", origen]
            else:
                comando = ["python3", DOWNLOAD,
                           "-d", os.path.join(bajadas, remoto)]
            comando += ["-H", IP_SERVIDOR, "-p", str(PUERTO),
                        "-n", remoto, "-r", protocolo]
            # La salida va a un archivo y no a un PIPE: nadie la drena
            # mientras los cuatro corren, y un pipe lleno trabaria al
            # cliente.
            salida = open(
                os.path.join(tempfile.gettempdir(),
                             "cliente-%s.log" % host),
                "w+",
            )
            lanzados.append({
                "host": host,
                "operacion": operacion,
                "remoto": remoto,
                "salida": salida,
                "proceso": net.get(host).popen(comando, stdout=salida,
                                               stderr=salida),
                "desde": time.monotonic(),
                "tardo": None,
            })

        # Se sondea a los cuatro y se anota el tiempo de cada uno en
        # cuanto termina. Esperarlos en orden de lanzamiento mediria el
        # maximo acumulado en vez de lo que tardo cada uno, y eso
        # inflaria el solapamiento que la prueba quiere demostrar.
        pendientes = list(lanzados)
        while pendientes:
            for tarea in list(pendientes):
                if tarea["proceso"].poll() is not None:
                    tarea["tardo"] = time.monotonic() - tarea["desde"]
                    pendientes.remove(tarea)
            if pendientes:
                time.sleep(0.02)
        total = time.monotonic() - arranque

        filas = []
        for tarea in lanzados:
            base = (storage if tarea["operacion"] == "upload"
                    else bajadas)
            final = os.path.join(base, tarea["remoto"])
            ok = os.path.exists(final) and _md5(final) == md5_origen
            filas.append((tarea["tardo"], ok))
            print("  %-3s %-8s %-18s %7.2f s  %s"
                  % (tarea["host"], tarea["operacion"], tarea["remoto"],
                     tarea["tardo"], "ok" if ok else "MAL"))
            if not ok:
                tarea["salida"].seek(0)
                print(tarea["salida"].read())
    finally:
        for tarea in lanzados:
            if tarea["proceso"].poll() is None:
                tarea["proceso"].terminate()
            tarea["salida"].close()
        servidor.terminate()
        archivo_log.close()
        shutil.copyfile(*rutas_log)

    suma = sum(fila[0] for fila in filas)
    fallaron = [fila for fila in filas if not fila[1]]

    print()
    print("Tiempo total:              %.2f s" % total)
    print("Suma de los individuales:  %.2f s" % suma)
    print("Solapamiento:              %.1fx" % (suma / max(total, 1e-9)))
    print()
    if fallaron:
        print("NO CUMPLE: %d de %d transferencias quedaron mal"
              % (len(fallaron), len(filas)))
    elif suma <= total:
        print("Las %d quedaron integras, pero no se solaparon: revisar"
              % len(filas))
    else:
        print("CUMPLE: %d transferencias simultaneas, las %d integras"
              % (len(filas), len(filas)))


def medir(net, perdida, rtt, verboso=True):
    """Sube y baja cada archivo con cada protocolo, y cronometra."""
    h1, h2 = net.get("h1"), net.get("h2")
    trabajo = os.path.join(RAIZ, "mediciones")
    rutas = preparar_archivos(trabajo)
    storage, bajadas = _preparar_directorios(trabajo)
    md5_origen = {n: _md5(r) for n, r in rutas.items()}

    servidor, archivo_log, rutas_log = _arrancar_servidor(
        h2, trabajo, storage, verboso
    )

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
        shutil.copyfile(*rutas_log)

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
    parser.add_argument("--concurrencia", action="store_true",
                        help="2 subidas y 2 bajadas en paralelo")
    parser.add_argument("--protocolo", default="sack",
                        choices=("sw", "sack"),
                        help="protocolo de --concurrencia (default: sack)")
    parser.add_argument("--silencioso", action="store_true",
                        help="servidor sin -v: mide sin el costo del log")
    return parser.parse_args()


def main():
    args = parsear()
    setLogLevel("info")

    net = Mininet(topo=TopoTP(perdida=args.perdida,
                              retardo_ms=args.rtt // 2),
                  link=TCLink, controller=None)
    net.start()
    try:
        print("perdida %d%% por sentido, RTT %d ms"
              % (args.perdida, args.rtt))
        if args.concurrencia:
            concurrencia(net, args.protocolo, not args.silencioso)
        elif args.medir:
            medir(net, args.perdida, args.rtt, not args.silencioso)
        else:
            print("Clientes:  %s    Servidor: h2 (%s)"
                  % (" ".join(CLIENTES), IP_SERVIDOR))
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
