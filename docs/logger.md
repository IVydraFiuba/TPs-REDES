# Guía Rápida: Uso del Logger (No usar `print`)

Para poder soportar los comandos `-v` (verbose) y `-q` (quiet) que pide el TP, **está prohibido usar `print()`** en el código. En su lugar, usaremos el módulo nativo `logging`.

La configuración fuerte (los argumentos y el formato) ya se hace en los archivos principales (`upload`, `download`, `start-server`). Si estás trabajando en las clases internas (dentro de `src/lib/`), **solo tienes que seguir estos 2 pasos**.

## 1. Importar y obtener el logger

Al principio de **cada archivo `.py`** donde vayas a escribir mensajes, agrega estas dos líneas:

```python
import logging

# Esto crea un logger asociado al nombre del archivo actual
logger = logging.getLogger(__name__)
```

## 2. Registrar mensajes según su importancia

Dependiendo de qué tan importante sea el mensaje, debes usar un método distinto. El sistema decidirá automáticamente si mostrarlo o no según los flags del usuario.

```python
# 🟢 DEBUG (Solo se ve si el usuario usa '-v')
# Úsalo para: Variables internas, nro de secuencia, tracking de ACKs, envíos de paquetes UDP.
logger.debug(f"Enviando paquete seq={paquete.seq} a {addr}")

# 🔵 INFO (Se ve por defecto o con '-v')
# Úsalo para: Hitos importantes del programa que el usuario normal necesita saber.
logger.info("Iniciando conexión con el servidor...")
logger.info("Transferencia de archivo completada (100%).")

# 🔴 ERROR (Se ve SIEMPRE, incluso en modo '-q' quiet)
# Úsalo para: Errores que rompen el flujo, timeouts irrecuperables.
logger.error("Se agotó el tiempo de espera. Abortando transferencia.")

# 💥 EXCEPTION (Úsalo solo dentro de bloques try/except)
# Hace lo mismo que .error(), pero además imprime toda la traza (el texto rojo de Python)
try:
    with open("archivo.txt", "rb") as f:
        pass
except FileNotFoundError:
    logger.exception("El archivo que intentas subir no existe.")
```

## 💡 Resumen visual de visibilidad

| Método que usas | Comando `-v` | Sin flags (Normal) | Comando `-q` |
| :--- | :---: | :---: | :---: |
| `logger.debug()` | ✅ Visible | ❌ Oculto | ❌ Oculto |
| `logger.info()` | ✅ Visible | ✅ Visible | ❌ Oculto |
| `logger.error()` | ✅ Visible | ✅ Visible | ✅ Visible |