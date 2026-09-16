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
python src/start-server -H <ADDR> -p <PORT> -s <DIRPATH>
```

Opciones disponibles:

| Flag              | Descripción                                       |
| ----------------- | ------------------------------------------------- |
| `-h`, `--help`    | Muestra la ayuda del comando.                     |
| `-v`, `--verbose` | Aumenta el nivel de detalle de la salida.         |
| `-q`, `--quiet`   | Reduce el nivel de detalle de la salida.          |
| `-H`, `--host`    | Dirección IP donde se ejecutará el servicio.      |
| `-p`, `--port`    | Puerto utilizado por el servidor.                 |
| `-s`, `--storage` | Directorio utilizado para almacenar los archivos. |


### Upload

Permite enviar un archivo desde el cliente hacia el servidor.

```bash
python src/upload -H <ADDR> -p <PORT> -s <FILEPATH> -n <FILENAME> -r <PROTOCOL>
```

Opciones disponibles:

| Flag               | Descripción                                              |
| ------------------ | -------------------------------------------------------- |
| `-h`, `--help`     | Muestra la ayuda del comando.                            |
| `-v`, `--verbose`  | Aumenta el nivel de detalle de la salida.                |
| `-q`, `--quiet`    | Reduce el nivel de detalle de la salida.                 |
| `-H`, `--host`     | Dirección IP del servidor.                               |
| `-p`, `--port`     | Puerto del servidor.                                     |
| `-s`, `--src`      | Ruta del archivo local que se desea enviar.              |
| `-n`, `--name`     | Nombre con el que se guardará el archivo en el servidor. |
| `-r`, `--protocol` | Protocolo de recuperación de errores a utilizar.         |



### Download

Permite descargar un archivo desde el servidor.

```bash
python src/download -H <HOST> -p <PORT> -d <FILEPATH> -n <FILENAME> -r <PROTOCOL>
```

Opciones disponibles:

| Flag               | Descripción                                      |
| ------------------ | ------------------------------------------------ |
| `-h`, `--help`     | Muestra la ayuda del comando.                    |
| `-v`, `--verbose`  | Aumenta el nivel de detalle de la salida.        |
| `-q`, `--quiet`    | Reduce el nivel de detalle de la salida.         |
| `-H`, `--host`     | Dirección IP del servidor.                       |
| `-p`, `--port`     | Puerto del servidor.                             |
| `-d`, `--dst`      | Ruta donde se guardará el archivo descargado.    |
| `-n`, `--name`     | Nombre del archivo que se desea descargar.       |
| `-r`, `--protocol` | Protocolo de recuperación de errores a utilizar. |

