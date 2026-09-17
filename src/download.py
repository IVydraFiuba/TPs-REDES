from lib.args import parsear_argumentos_descarga

# TODO(Persona 5): cliente real.
#   - protocol.conectar(...) con -r mapeado por PROTOCOLS; luego send/recv
#   - (aparte) topologia mininet, capturas y analisis SACK vs S&W
# Ejemplo: python src/download.py -H 127.0.0.1 -p 8080 -d ./foto.jpg -n foto.jpg -r sw


def print_debug_args(args):
    print(f"Verbose: {args.verbose}")
    print(f"Quiet: {args.quiet}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"FILEPATH: {args.dst}")
    print(f"FILENAME: {args.name}")
    print(f"Protocol: {args.protocol}")


if __name__ == "__main__":
    args = parsear_argumentos_descarga()
    print_debug_args(args)
    # Codigo aca
