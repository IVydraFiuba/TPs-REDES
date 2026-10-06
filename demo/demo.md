# Demo: comandos en orden

**Todo se ejecuta desde la raíz del proyecto. No entrar a `demo/`.**

Usamos dos terminales normales:

- **Terminal 1:** levantar Mininet y manejar su consola.
- **Terminal 2:** preparar archivos y mostrar hashes.

Desde Mininet abrimos cinco xterm: **servidor**, **subida1**, **subida2**, **descarga1** y **descarga2**. Heredan el directorio desde el que levantamos la topología. Los comandos de cada xterm se escriben sin prefijo `h1`, `h2`, etc.

## 0. Preparar archivos

En la **Terminal 2**, antes de iniciar el servidor:

```bash
sudo python3 demo/clear.py
cp demo/archivos_para_subir/5mb.jpg demo/h1_subida/5mb.jpg
cp demo/archivos_para_subir/5mb.jpg demo/h3_subida/5mb.jpg
```

Preparar una vez un archivo de exactamente 1 MiB para la última prueba:

```bash
python3 - <<'PY'
from pathlib import Path
import os
p = Path('demo/archivos_para_subir/1MiB.bin')
if not p.exists():
    p.write_bytes(os.urandom(1048576))
assert p.stat().st_size == 1048576, 'El archivo existente no tiene 1 MiB'
PY
```

`clear.py` vacía los almacenamientos de servidor y clientes, pero conserva los originales de `archivos_para_subir/`. No ejecutarlo durante transferencias.

## 1. Levantar la topología y verificar conectividad

En la **Terminal 1**:

```bash
sudo python3 demo/mininet/topologia.py --perdida 10 --rtt 40
```

Cuando aparezca `mininet>`, ejecutar:

```text
net
h1 ping -c 30 -i 0.2 10.0.0.2
```

El script configura **10 % de pérdida por sentido y 20 ms de ida + 20 ms de vuelta** entre cada cliente y el servidor h2. El RTT de ping debe rondar 40 ms.



## 2. Abrir y nombrar los xterm

En **Mininet**, dentro de la Terminal 1:

```text
xterm h2 h1 h3 h4 h5
```

En cada ventana ejecutar su comando de título una sola vez:

| Host | Nombre | Comando dentro de su xterm |
| --- | --- | --- |
| h2 | servidor | `printf '\033]0;servidor\007'` |
| h1 | subida1 | `printf '\033]0;subida1\007'` |
| h3 | subida2 | `printf '\033]0;subida2\007'` |
| h4 | descarga1 | `printf '\033]0;descarga1\007'` |
| h5 | descarga2 | `printf '\033]0;descarga2\007'` |


En **servidor**:

```bash
python3 src/start-server.py -H 10.0.0.2 -p 8080 -s demo/almacenamiento_servidor
```

Dejarlo corriendo. El almacenamiento de cada cliente se identifica por su host: `h1_subida`, `h3_subida`, `h4_descarga` y `h5_descarga`.

## 3. Subir 5 MB con SACK y verificar el hash

En **subida1**:

```bash
time python3 src/upload.py -H 10.0.0.2 -p 8080 -s demo/h1_subida/5mb.jpg -n base-5mb.jpg -r sack
```

Esperar a que termine. El tiempo **`real` debe ser menor que 2m0s**. El archivo disponible tiene 5.245.329 bytes, superior a 5 MB decimales.

En la **Terminal 2**:

```bash
sha256sum demo/archivos_para_subir/5mb.jpg demo/almacenamiento_servidor/base-5mb.jpg
```
Los dos hashes deben coincidir. Si la aplicación informa un error o los hashes difieren, detener la prueba y revisar antes de continuar.


## 4. Concurrencia: dos uploads y dos downloads simultáneos

**No limpiar el servidor.** Las descargas usarán `base-5mb.jpg`, que ya subimos y verificamos.

Preparar los cuatro comandos y ejecutarlos seguidos, **sin esperar a que termine el anterior**.

En **subida1**:

```bash
time python3 src/upload.py -H 10.0.0.2 -p 8080 -s demo/h1_subida/5mb.jpg -n concurrente-h1.jpg -r sack
```

En **subida2**, inmediatamente:

```bash
time python3 src/upload.py -H 10.0.0.2 -p 8080 -s demo/h3_subida/5mb.jpg -n concurrente-h3.jpg -r sack
```

En **descarga1**, inmediatamente:

```bash
time python3 src/download.py -H 10.0.0.2 -p 8080 -n base-5mb.jpg -d demo/h4_descarga/5mb.jpg -r sack
```

En **descarga2**, inmediatamente:

```bash
time python3 src/download.py -H 10.0.0.2 -p 8080 -n base-5mb.jpg -d demo/h5_descarga/5mb.jpg -r sack
```

Los cuatro deben estar ejecutándose a la vez. Si alguno termina antes de iniciar el último, preparar mejor las ventanas y repetir con nombres nuevos. En Wireshark se puede comprobar el tráfico simultáneo de los cuatro clientes.

Esperar a que **terminen los cuatro**. En la **Terminal 2**:

```bash
sha256sum demo/archivos_para_subir/5mb.jpg demo/almacenamiento_servidor/concurrente-h1.jpg demo/almacenamiento_servidor/concurrente-h3.jpg demo/h4_descarga/5mb.jpg demo/h5_descarga/5mb.jpg
```

Los cinco hashes deben coincidir. Esta prueba usa SACK en los cuatro clientes; para demostrar también protocolos mezclados, se puede repetir cambiando el upload de subida2 a `-r sw` (tardará más).

## 5. Reiniciar con el retardo indicado

Cuando hayan terminado las transferencias:

1. En **servidor**, pulsar **Ctrl+C**.
2. En la consola **Mininet de la Terminal 1**, ejecutar:

```text
exit
```

No limpiar los archivos todavía.

En la **Terminal 1**, levantar nuevamente la red. Ejemplo si piden **RTT 300 ms**:

```bash
sudo python3 demo/mininet/topologia.py --perdida 10 --rtt 300
```
Reemplazar `300` por el RTT solicitado. 

En **Mininet**:

```text
h1 ping -c 30 -i 0.2 10.0.0.2
xterm h2 h1
```

Usar las **ventanas nuevas**. En el nuevo xterm de **h2**:

```bash
printf '\033]0;servidor\007'
python3 src/start-server.py -H 10.0.0.2 -p 8080 -s demo/almacenamiento_servidor
```

## 6. Transferir 1 MiB y verificar retransmisiones

Antes de ejecutar la transferencia, iniciar la captura desde la app de Wireshark en la interfaz correspondiente a la nueva topología.

En **subida1**:

```bash
time python3 src/upload.py -H 10.0.0.2 -p 8080 -s demo/archivos_para_subir/1MiB.bin -n nuevo-rtt-1MiB.bin -r sack
```

Esperar a que termine. En la **Terminal 2**:

```bash
sha256sum demo/archivos_para_subir/1MiB.bin demo/almacenamiento_servidor/nuevo-rtt-1MiB.bin
```

Los dos hashes deben coincidir. Detener la captura en Wireshark y mostrar las retransmisiones.


