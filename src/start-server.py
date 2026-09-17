from lib.args import parsear_argumentos_servidor

# TODO(Parte 4): servidor real.
#   - escuchar; usar protocol.recibir_handshake / responder_handshake
#   - chequear archivo/espacio (condiciones de error), guardar en storage
#   - obtener canal con crear_transport; un thread por cliente (concurrencia)
#  Ejemplo: python src/start-server.py -H 127.0.0.1 -p 8080 -s ./storage


def print_debug_args(args):
    print(f"Verbose: {args.verbose}")
    print(f"Quiet: {args.quiet}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Storage: {args.storage}")


if __name__ == "__main__":
    args = parsear_argumentos_servidor()
    print_debug_args(args)
    # Codigo aca
    # recibir handshake, responder handshake, crear transport
    # chequear archivo espacio y guardar
    # un solo thread por cliente
