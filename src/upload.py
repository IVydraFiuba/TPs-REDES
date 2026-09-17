from lib.args import parsear_argumentos_subida


def print_debug_args(args):
    print(f"Verbose: {args.verbose}")
    print(f"Quiet: {args.quiet}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"FILEPATH: {args.src}")
    print(f"FILENAME: {args.name}")
    print(f"Protocol: {args.protocol}")



if __name__ == "__main__":
    args = parsear_argumentos_subida()
    print_debug_args(args)
