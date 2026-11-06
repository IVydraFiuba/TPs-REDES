# Informe del TP: SDN y NAT

## Descripción general de la solución

## Diseño de la tabla NAT

## Manejo de ARP

El controlador implementa un manejo propio de ARP para comportarse como router entre la red privada y la red pública. El protocolo ARP se utiliza en dos situaciones principales:

* Para responder a los hosts que preguntan por la IP del router.
* Para resolver dinámicamente la MAC de los hosts públicos antes de reenviar tráfico hacia ellos.

En nuestra solución, el switch tiene dos interfaces:

```text
IP privada del router: 192.168.1.254
MAC privada del router: 00:00:00:bb:bb:bb

IP pública del router: 200.0.0.254
MAC pública del router: 00:00:00:aa:aa:aa
```

Estas direcciones representan al router en cada lado de la red. Para los hosts privados, el gateway es `192.168.1.254`, mientras que para los hosts públicos es el `200.0.0.254`.

### 1. Tabla ARP

La tabla ARP está administrada en el controlador mediante el diccionario `arp_table`. Su objetivo es guardar las asociaciones entre direcciones IP y direcciones MAC aprendidas en tiempo de ejecución.

Conceptualmente, la tabla tiene la siguiente estructura:

```text
IP -> (MAC, última vez visto)

192.168.1.2 -> (00:00:00:00:00:02, 1730000000.0)
200.0.0.1   -> (00:00:00:00:00:01, 1730000004.2)
```

#### ¿Cuándo se actualiza la tabla ARP?

El controlador actualiza la `arp_table` en dos momentos:

1. **Al recibir un `ARP REQUEST`:** Cuando un host de la red envía una consulta ARP preguntando por la IP del gateway (por ejemplo, h2 buscando la MAC de 192.168.1.254), la trama pasa por el controlador. En ese instante, el método handle_arp inspecciona los campos del emisor (protosrc y hwsrc) e inserta de forma inmediata esa IP y MAC en la arp_table. Este mecanismo permite aprender las direcciones de los hosts locales sin costo adicional y sin necesidad de emitir peticiones adicionales por la red.
2. **Al recibir un `ARP REPLY`:** Cuando un paquete IP tiene como destino una dirección MAC desconocida, el controlador genera y emite una solicitud ARP REQUEST proactiva hacia la red pública. Cuando el host de destino responde mediante una trama ARP REPLY, el controlador intercepta el mensaje en la rama correspondiente de handle_arp, extrae la asociación (IP → MAC) y la registra en la arp_table. Inmediatamente después de actualizar la tabla, el controlador utiliza esta entrada para despachar los paquetes que se encontraban retenidos en el buffer.

#### Vencimiento de entradas

Cada entrada vence si pasan más de `ARP_TIMEOUT = 20` s (`config.py`) sin ver un ARP de esa IP. Cada ARP visto la refresca.

El vencimiento se evalúa en `resolve_mac`: si la entrada venció, se borra, se loguea `ARP VENCIDO` y se trata como desconocida (se retiene el paquete y se envía un `ARP REQUEST`). No usamos un `Timer`: con pocos hosts alcanza con revisar la entrada al consultarla.

El valor se eligió para el entorno de prueba: es mayor que el `idle_timeout` de los flujos (10 s) y lo bastante corto para ver el vencimiento en una demo. Los dos timeouts son independientes: con un flujo instalado, el switch reenvía sin consultar al controlador.

No hay reintentos de `ARP REQUEST` ni timeout para `packet_buffer`.

### 2. Retención de paquetes pendientes

Mientras el controlador espera el `ARP REPLY` de un host externo, no descarta el paquete IP original. En su lugar, retiene el evento OpenFlow en el diccionario `packet_buffer`.

El `packet_buffer` se representa como:

```text
IP destino -> lista de eventos pendientes

200.0.0.1 -> [pending_event_1, pending_event_2]
```

#### Manejo de consultas (`resolve_mac`)

1. **Petición única:** Al llegar el primer paquete para una IP desconocida, se guarda en el buffer y se envía un `ARP REQUEST` broadcast (`Who has X? Tell 200.0.0.254`).
2. **Evitar solicitudes duplicadas:** Si llegan nuevos paquetes hacia la misma IP antes de recibir la respuesta, se encolan en la lista de la IP correspondiente sin reenviar otro paquete ARP.
3. **Despacho de tráfico:** Al recibir el `ARP REPLY`, se registra la MAC en `arp_table`, se procesan e instalan las reglas de flujo para todos los eventos retenidos de esa IP, y finalmente se elimina la entrada del buffer.

## Estrategia de instalación de flujos

## Decisiones de diseño

### Organización de archivos

Separamos el controlador por responsabilidad para poder trabajar sobre ARP, PAT y las reglas sin concentrar todo en `protorouter.py`.

```text
TPs-REDES/
├── topo.py                         # Crea la red en Mininet
├── topo_config.json                # Direcciones, gateways y conexiones
├── pox/
│   ├── pox.py                      # Lanzador de POX
│   └── ext/
│       ├── protorouter.py           # Entrada y coordinación del router
│       └── tp_router/
│           ├── config.py           # Lee el JSON y configura los logs
│           ├── ARP.py              # Resolución ARP y paquetes pendientes
│           ├── PAT.py              # Traducción NAT por puertos 
│           └── flujos.py           # Reglas OpenFlow y forwarding actual
```

- **`protorouter.py`:** punto de entrada del controlador. Registra los eventos OpenFlow y coordina el procesamiento de paquetes con los módulos de ARP y flujos.
- **`config.py`:** lee `topo_config.json`, convierte las direcciones a los tipos de POX y define los valores compartidos del router. También configura el logger y los colores de sus mensajes.
- **`ARP.py`:** administra la tabla ARP, responde consultas por las IP del router y genera solicitudes para resolver las MAC de los hosts. Retiene los paquetes que esperan una resolución ARP.
- **`PAT.py`:** administra las tablas de traducción y la asignación de puertos públicos para identificar las conexiones de los clientes privados.
- **`flujos.py`:** construye e instala las reglas OpenFlow de salida y retorno, y reenvía el primer paquete de cada flujo.
- **`topo.py`:** crea los hosts, el switch y sus enlaces en Mininet a partir de `topo_config.json`.
- **`topo_config.json`:** define las IP, MAC, gateways y puertos del switch que utilizan la topología y el controlador.

### Configuración y topología

Centralizamos las direcciones y conexiones en [`topo_config.json`](../../topo_config.json) para que Mininet y POX usen los mismos valores. Esto evita duplicarlos en el código y permite cambiar la topología desde un solo archivo.

En `gateways` se definen la IP con prefijo y la MAC de las interfaces pública y privada del NAT. En `hosts`, cada equipo indica su nombre, IP con prefijo, MAC, red (`private` o `public`) y puerto del switch (`switch_port`). Para agregar un cliente, se añade una entrada con IP, MAC y puerto libres. La configuración actual admite varios clientes privados y un único enlace público.

Después de editar el JSON, hay que reiniciar Mininet y POX. Para actualizar el diagrama, se ejecuta `python3 tools/generar_imagen_topologia.py` desde la raíz del repositorio.

## Problemas encontrados y soluciones implementadas

## Pruebas realizadas

### Conectividad básica

### Múltiples clientes
Para el manejo de múltiples clientes se añadió a la topologia inicial los puertos `h3` y `h4` cada uno en su red privada.

![Topología con servidor público y tres clientes privados](img/topologia.png)

| Host | Red | IP | MAC | Gateway | Puerto de s1 |
| --- | --- | --- | --- | --- | --- |
| h1 | Pública | 200.0.0.1/24 | 00:00:00:00:00:01 | 200.0.0.254 | 1 |
| h2 | Privada | 192.168.1.2/24 | 00:00:00:00:00:02 | 192.168.1.254 | 2 |
| h3 | Privada | 192.168.1.3/24 | 00:00:00:00:00:03 | 192.168.1.254 | 3 |
| h4 | Privada | 192.168.1.4/24 | 00:00:00:00:00:04 | 192.168.1.254 | 4 |

Se realizaron las mismas pruebas que con `h2` para ambos puertos
```
mininet> h3 ping -c 1 h1
PING 200.0.0.1 (200.0.0.1) 56(84) bytes of data.
64 bytes from 200.0.0.1: icmp_seq=1 ttl=64 time=3.08 ms

--- 200.0.0.1 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 3.078/3.078/3.078/0.000 ms
``` 
```
INFO:protorouter:RECIBIDO: 192.168.1.3 → 200.0.0.1 | MAC: 00:00:00:00:00:03 → 00:00:00:bb:bb:bb | In Port: 3
INFO:protorouter:MATCH: 192.168.1.3 pertenece a la red privada 192.168.1.0/24
INFO:protorouter:ENVIANDO: 192.168.1.3 → 200.0.0.1 | MAC: 00:00:00:aa:aa:aa → 00:00:00:00:00:01 | Out Port: 1
```

```
mininet> h4 ping -c 1 h1
PING 200.0.0.1 (200.0.0.1) 56(84) bytes of data.
64 bytes from 200.0.0.1: icmp_seq=1 ttl=64 time=2.51 ms

--- 200.0.0.1 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 2.509/2.509/2.509/0.000 ms
```
```
INFO:protorouter:RECIBIDO: 192.168.1.4 → 200.0.0.1 | MAC: 00:00:00:00:00:04 → 00:00:00:bb:bb:bb | In Port: 4
INFO:protorouter:MATCH: 192.168.1.4 pertenece a la red privada 192.168.1.0/24
INFO:protorouter:ENVIANDO: 192.168.1.4 → 200.0.0.1 | MAC: 00:00:00:aa:aa:aa → 00:00:00:00:00:01 | Out Port: 1
```

### Diferentes tipos de tráfico

## Conclusión
