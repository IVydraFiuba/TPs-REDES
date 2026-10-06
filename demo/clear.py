#!/usr/bin/env python3
"""Vacía únicamente los almacenamientos de práctica junto a este script."""

import argparse
from pathlib import Path
import shutil


DIRECTORIOS = (
    "almacenamiento_servidor",
    "h1_subida",
    "h3_subida",
    "h4_descarga",
    "h5_descarga",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--listar", action="store_true",
        help="muestra qué se borraría, sin modificar archivos",
    )
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    destinos = [base / nombre for nombre in DIRECTORIOS]
    # Validar todos antes de borrar; nunca seguir un almacenamiento enlazado.
    for destino in destinos:
        if destino.is_symlink() or (destino.exists() and not destino.is_dir()):
            parser.error(f"El almacenamiento no es un directorio real: {destino}")

    for destino in destinos:
        if not destino.exists():
            if not args.listar:
                destino.mkdir()
                (destino / ".gitkeep").touch()
            continue
        for entrada in sorted(destino.iterdir()):
            if entrada.name == ".gitkeep" and entrada.is_file() and not entrada.is_symlink():
                continue
            print(f"{'Borraría' if args.listar else 'Borrando'}: {entrada}")
            if args.listar:
                continue
            if entrada.is_symlink() or not entrada.is_dir():
                entrada.unlink()
            else:
                shutil.rmtree(entrada)
    print("Originales de archivos_para_subir conservados.")


if __name__ == "__main__":
    main()
