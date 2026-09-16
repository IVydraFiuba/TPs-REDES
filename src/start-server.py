from lib.args import parsear_argumentos_servidor


def print_debug_args(args):
    print(f"Verbose: {args.verbose}")
    print(f"Quiet: {args.quiet}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Storage: {args.storage}")


if __name__ == "__main__":
    args = parsear_argumentos_servidor()
    print_debug_args(args)
