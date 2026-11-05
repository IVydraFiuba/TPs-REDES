# Informe del TP: SDN y NAT

## Descripción general de la solución

## Diseño de la tabla NAT

## Manejo de ARP

## Estrategia de instalación de flujos

## Decisiones de diseño

## Problemas encontrados y soluciones implementadas

## Pruebas realizadas

### Conectividad básica

### Múltiples clientes
Para el manejo de múltiples clientes se añadió al archivo `topo.py` los puertos `h3` y `h4` cada uno en su red privada.

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
