# TPs-REDES

Trabajos prácticos de la materia **Redes (TA048)** — FIUBA.

## Instalación

Crear un entorno virtual de Python
Activar el entorno
Instalar las dependencias
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si el entorno virtual ya fue creado anteriormente, solo es necesario activarlo
```bash
source .venv/bin/activate
```

## Test

Ejecutar todos los tests
```
python -m pytest
```

Ejecutar tests de un archivo específico
```
python -m pytest tests/lib/test_args.py
```

## Linter PEP8

El proyecto utiliza `flake8` para verificar el cumplimiento de PEP8.

Analizar todo el proyecto:

```bash
flake8 .
```

Analizar un archivo en particular:

```bash
flake8 src/lib/ejemplo.py
```

## Uso

La aplicación cuenta con tres comandos principales:

* `upload`: subir un archivo al servidor.
* `download`: descargar un archivo desde el servidor.
* `start-server`: iniciar el servidor.

### Servidor

Iniciar el servidor:

```bash
python src/start-server.py -H ADDR -p PORT -s DIRPATH
```

Opciones disponibles:

| Flag              | Descripción                     |
| ----------------- | ------------------------------- |
| `-h`, `--help`    | show this help message and exit |
| `-v`, `--verbose` | increase output verbosity       |
| `-q`, `--quiet`   | decrease output verbosity       |
| `-H`, `--host`    | service IP address              |
| `-p`, `--port`    | service port                    |
| `-s`, `--storage` | storage dir path                |


### Upload

Permite enviar un archivo desde el cliente hacia el servidor.

```bash
python src/upload.py -H ADDR -p PORT -s FILEPATH -n FILENAME -r protocol
```

Opciones disponibles:

| Flag               | Descripción                     |
| ------------------ | ------------------------------- |
| `-h`, `--help`     | show this help message and exit |
| `-v`, `--verbose`  | increase output verbosity       |
| `-q`, `--quiet`    | decrease output verbosity       |
| `-H`, `--host`     | server IP address               |
| `-p`, `--port`     | server port                     |
| `-s`, `--src`      | source file path                |
| `-n`, `--name`     | file name                       |
| `-r`, `--protocol` | error recovery protocol         |



### Download

Permite descargar un archivo desde el servidor.

```bash
python src/download.py -H ADDR -p PORT -d FILEPATH -n FILENAME -r protocol
```

Opciones disponibles:

| Flag               | Descripción                     |
| ------------------ | ------------------------------- |
| `-h`, `--help`     | show this help message and exit |
| `-v`, `--verbose`  | increase output verbosity       |
| `-q`, `--quiet`    | decrease output verbosity       |
| `-H`, `--host`     | server IP address               |
| `-p`, `--port`     | server port                     |
| `-d`, `--dst`      | destination file path           |
| `-n`, `--name`     | file name                       |
| `-r`, `--protocol` | error recovery protocol         |
