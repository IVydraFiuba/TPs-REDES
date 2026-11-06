# Un GET HTTP de h2 a h1 a través del protorouter

Ejemplo del comportamiento esperado del TP. Las cachés ARP arrancan vacías. h1 escucha en TCP 80. Para seguir una conexión concreta, h2 elige TCP 50000 y POX reservará TCP 40000.

| Actor o interfaz | IPv4 | MAC | Configuración relevante |
| --- | --- | --- | --- |
| h2 | 192.168.1.2/24 | 00:00:00:00:00:02 | Gateway 192.168.1.254 · conectado al puerto 2 de s1 |
| Interfaz privada del protorouter | 192.168.1.254/24 | 00:00:00:bb:bb:bb | Gateway de h2 |
| Interfaz pública del protorouter | 200.0.0.254/24 | 00:00:00:aa:aa:aa | Gateway de h1 |
| h1 | 200.0.0.1/24 | 00:00:00:00:00:01 | Gateway 200.0.0.254 · conectado al puerto 1 de s1 |

**s1 es el plano de datos**. Recibe tramas, consulta su tabla de flujos y ejecuta acciones. 
**POX es el plano de control**. Guarda la caché ARP del protorouter y la tabla PAT, y programa s1 por un canal OpenFlow. 

En este ejemplo, s1 envía a POX las tramas sin regla y POX retiene una copia completa cuando necesita esperar.

## 1. h2 resuelve la MAC del gateway privado

### 1.1 · h2 → s1

h2 prepara un SYN para 200.0.0.1.

Su máscara /24 ubica a h1 fuera de su red. 
La ruta por defecto indica el próximo salto 192.168.1.254, pero su caché ARP está vacía.  (NO conoce la MAC del gateway: 192.168.1.254)

Deja el SYN pendiente y emite esta consulta ARP request por broadcast. (Busca la MAC para poder mandar su SYN)

| Campo | Valor |
| --- | --- |
| Ethernet · MAC origen | 00:00:00:00:00:02 |
| Ethernet · MAC destino | ff:ff:ff:ff:ff:ff |
| EtherType | 0x0806 (ARP) |
| ARP · operación | Request (1) |
| ARP · IP del emisor | 192.168.1.2 |
| ARP · MAC del emisor | 00:00:00:00:00:02 |
| ARP · IP objetivo | 192.168.1.254 |
| ARP · MAC objetivo | 00:00:00:00:00:00 |  (marca que no sabe la MAC de ese IP)

### 1.2 · s1 → POX

s1 recibe el broadcast por el enlace de h2.

Como carece de una regla para atender esa consulta, entrega la trama y su puerto de entrada al controlador.

| Campo | Valor |
| --- | --- |
| OpenFlow | PacketIn |
| Puerto de entrada en s1 | 2 |
| Trama incluida | ARP Request de 1.1 |

POX reconoce su IP privada en el campo objetivo. Del emisor aprende esta entrada antes de responder.

| Caché ARP de POX · IP | MAC aprendida |
| --- | --- |
| 192.168.1.2 | 00:00:00:00:00:02 |

Aprender que H2 tiene esa IP y esa MAC por que tenia esos datos en la trama del ARP request


### 1.3 · POX → s1

POX construye la respuesta con la MAC de su interfaz privada. 
Usa el puerto de entrada del PacketIn para indicarle a s1 por dónde devolverla.

| Campo | Valor |
| --- | --- |
| OpenFlow | PacketOut |
| Trama incluida | ARP Reply detallado en 1.4 |
| Acciones | Emitir por el puerto 2 |

### 1.4 · s1 → h2

s1 ejecuta la orden. Puede enviar la ARP reply directamente a la MAC que h2 incluyó en su consulta.

| Campo | Valor |
| --- | --- |
| Ethernet · MAC origen | 00:00:00:bb:bb:bb |
| Ethernet · MAC destino | 00:00:00:00:00:02 |
| EtherType | 0x0806 (ARP) |
| ARP · operación | Reply (2) |
| ARP · IP del emisor | 192.168.1.254 |
| ARP · MAC del emisor | 00:00:00:bb:bb:bb |
| ARP · IP objetivo | 192.168.1.2 |
| ARP · MAC objetivo | 00:00:00:00:00:02 |

h2 lee los campos del emisor y guarda la asociación que necesitaba para enviar el SYN.

| Caché ARP de h2 · IP | MAC aprendida |
| --- | --- |
| 192.168.1.254 | 00:00:00:bb:bb:bb |

## 2. El primer SYN llega al controlador

### 2.1 · h2 → s1

h2 ya puede construir la trama. La dirige a la MAC del gateway, mientras el paquete IPv4 lleva la IP de h1 como destino.

| Campo | Valor |
| --- | --- |
| Ethernet · MAC origen | 00:00:00:00:00:02 |
| Ethernet · MAC destino | 00:00:00:bb:bb:bb |  (MAC del gateway)
| IPv4 · origen | 192.168.1.2 |
| IPv4 · destino | 200.0.0.1 |   (IP del H1 )
| TCP · puerto origen | 50000 | (Puerto origen de H2)
| TCP · puerto destino | 80 |
| TCP · flags | SYN |

### 2.2 · s1 → POX

La conexión es nueva y s1 todavía carece de una regla de ida. 
POX recibe el SYN, identifica la conexión por sus direcciones, protocolo y puertos, y reserva un puerto público disponible.

| Campo | Valor |
| --- | --- |
| OpenFlow | PacketIn |
| Puerto de entrada en s1 | 2 |
| Trama incluida | SYN de 2.1 |

**Tabla PAT de POX** (ejemplo de una posible implementacion)

| Protocolo | Cliente privado | Dirección traducida | Servidor |
| --- | --- | --- | --- |
| TCP | 192.168.1.2:50000 | 200.0.0.254:40000 | 200.0.0.1:80 |

## 3. POX resuelve la MAC del servidor público

### 3.1 · POX → s1

POX conoce la IP de h1 y el puerto público de s1. 

Todavía le falta la MAC destino para reenviar el SYN. 
Guarda el SYN junto con su puerto de entrada y ordena emitir una ARP request en la red pública.

| Campo | Valor |
| --- | --- |
| OpenFlow | PacketOut |
| Trama incluida | ARP Request detallado en 3.2 |
| Acciones | Emitir por el puerto 1 |

### 3.2 · s1 → red pública (h1)

s1 emite la trama por el puerto 1. 
h1 reconoce su propia IP en el campo objetivo y aprende la dirección del gateway a partir del emisor.

| Campo | Valor |
| --- | --- |
| Ethernet · MAC origen | 00:00:00:aa:aa:aa |
| Ethernet · MAC destino | ff:ff:ff:ff:ff:ff |
| EtherType | 0x0806 (ARP) |
| ARP · operación | Request (1) |
| ARP · IP del emisor | 200.0.0.254 |
| ARP · MAC del emisor | 00:00:00:aa:aa:aa |
| ARP · IP objetivo | 200.0.0.1 |
| ARP · MAC objetivo | 00:00:00:00:00:00 |

### 3.3 · h1 → s1

h1 contesta a la MAC pública que acaba de aprender e incluye su propia MAC para que el protorouter pueda entregarle el SYN.

| Campo | Valor |
| --- | --- |
| Ethernet · MAC origen | 00:00:00:00:00:01 |
| Ethernet · MAC destino | 00:00:00:aa:aa:aa |
| EtherType | 0x0806 (ARP) |
| ARP · operación | Reply (2) |
| ARP · IP del emisor | 200.0.0.1 |
| ARP · MAC del emisor | 00:00:00:00:00:01 |
| ARP · IP objetivo | 200.0.0.254 |
| ARP · MAC objetivo | 00:00:00:aa:aa:aa |

### 3.4 · s1 → POX

s1 entrega la respuesta a POX. 
El controlador aprende la MAC de h1 y recupera el SYN que estaba esperando esa resolución.

| Campo | Valor |
| --- | --- |
| OpenFlow | PacketIn |
| Puerto de entrada en s1 | 1 |
| Trama incluida | ARP Reply de 3.3 |

| Actor | IP en su caché ARP | MAC |
| --- | --- | --- |
| h2 | 192.168.1.254 | 00:00:00:bb:bb:bb |
| POX | 192.168.1.2 | 00:00:00:00:00:02 |
| POX | 200.0.0.1 | 00:00:00:00:00:01 |
| h1 | 200.0.0.254 | 00:00:00:aa:aa:aa |

## 4. POX programa s1 y libera el SYN

### 4.1 · POX → s1, regla de ida

POX indica cómo reconocer los segmentos de h2 y traducir su origen.

| Campo | Valor |
| --- | --- |
| OpenFlow | FlowMod · agregar regla |
| Coincidencia · puerto de entrada | 2 |
| Coincidencia · protocolos | IPv4 / TCP |
| Coincidencia · origen | 192.168.1.2:50000 |
| Coincidencia · destino | 200.0.0.1:80 |
| Acción PAT | Reescribir origen a 200.0.0.254:40000 |
| Acción Ethernet · MAC origen | 00:00:00:aa:aa:aa |
| Acción Ethernet · MAC destino | 00:00:00:00:00:01 |
| Acción de salida | Puerto 1 |

### 4.2 · POX → s1, regla de vuelta

POX prepara el camino inverso antes de entregar el SYN. Cuando h1 responda al puerto público 40000, s1 podrá identificar al cliente privado.

| Campo | Valor |
| --- | --- |
| OpenFlow | FlowMod · agregar regla |
| Coincidencia · puerto de entrada | 1 |
| Coincidencia · protocolos | IPv4 / TCP |
| Coincidencia · origen | 200.0.0.1:80 |
| Coincidencia · destino | 200.0.0.254:40000 |
| Acción PAT | Reescribir destino a 192.168.1.2:50000 |
| Acción Ethernet · MAC origen | 00:00:00:bb:bb:bb |
| Acción Ethernet · MAC destino | 00:00:00:00:00:02 |
| Acción de salida | Puerto 2 |

### 4.3 · POX → s1

Las reglas ya describen cómo procesar los próximos segmentos. Para despachar el primero, que quedó en POX, el controlador lo envía a s1 con las acciones de ida.

| Campo | Valor |
| --- | --- |
| OpenFlow | PacketOut |
| Trama incluida | SYN original retenido en 2.2 |
| Acciones | Aplicar las reescrituras de 4.1 y emitir por el puerto 1 |

### 4.4 · s1 → h1

s1 ejecuta las acciones. h1 recibe el SYN en su puerto 80 y ve la dirección pública del protorouter como origen.

| Campo | Valor |
| --- | --- |
| Ethernet · MAC origen | 00:00:00:aa:aa:aa |
| Ethernet · MAC destino | 00:00:00:00:00:01 |
| IPv4 · origen | 200.0.0.254 |
| IPv4 · destino | 200.0.0.1 |
| TCP · puerto origen | 40000 |
| TCP · puerto destino | 80 |
| TCP · flags | SYN |

## 5. TCP completa la conexión y transporta el GET

### 5.1 · h1 acepta la conexión

h1 responde al origen que vio en el SYN. La regla de vuelta reconoce el puerto público y restaura el destino privado.

| Campo | h1 → s1 | s1 → h2 |
| --- | --- | --- |
| Ethernet · MAC origen | 00:00:00:00:00:01 | 00:00:00:bb:bb:bb |
| Ethernet · MAC destino | 00:00:00:aa:aa:aa | 00:00:00:00:00:02 |
| IPv4 · origen | 200.0.0.1 | 200.0.0.1 |
| IPv4 · destino | 200.0.0.254 | 192.168.1.2 |
| TCP · puerto origen | 80 | 80 |
| TCP · puerto destino | 40000 | 50000 |
| TCP · flags relevantes | SYN, ACK | SYN, ACK |
| Datos TCP (primera línea si hay HTTP) | Sin datos | Sin datos |

### 5.2 · h2 confirma

h2 reconoce el SYN de h1. La regla de ida traduce el ACK y h1 completa el establecimiento de la conexión.

| Campo | h2 → s1 | s1 → h1 |
| --- | --- | --- |
| Ethernet · MAC origen | 00:00:00:00:00:02 | 00:00:00:aa:aa:aa |
| Ethernet · MAC destino | 00:00:00:bb:bb:bb | 00:00:00:00:00:01 |
| IPv4 · origen | 192.168.1.2 | 200.0.0.254 |
| IPv4 · destino | 200.0.0.1 | 200.0.0.1 |
| TCP · puerto origen | 50000 | 40000 |
| TCP · puerto destino | 80 | 80 |
| TCP · flags relevantes | ACK | ACK |
| Datos TCP (primera línea si hay HTTP) | Sin datos | Sin datos |

### 5.3 · h2 solicita el recurso

h2 entrega la solicitud HTTP a TCP. El segmento coincide con la misma regla de ida porque pertenece a la conexión ya establecida.

| Campo | h2 → s1 | s1 → h1 |
| --- | --- | --- |
| Ethernet · MAC origen | 00:00:00:00:00:02 | 00:00:00:aa:aa:aa |
| Ethernet · MAC destino | 00:00:00:bb:bb:bb | 00:00:00:00:00:01 |
| IPv4 · origen | 192.168.1.2 | 200.0.0.254 |
| IPv4 · destino | 200.0.0.1 | 200.0.0.1 |
| TCP · puerto origen | 50000 | 40000 |
| TCP · puerto destino | 80 | 80 |
| TCP · flags relevantes | ACK | ACK |
| Datos TCP (primera línea si hay HTTP) | GET / HTTP/1.1 | GET / HTTP/1.1 |

### 5.4 · h1 responde al GET

h1 envía la respuesta HTTP por la conexión abierta. s1 aplica la regla de vuelta y h2 recibe los datos en TCP 50000.

| Campo | h1 → s1 | s1 → h2 |
| --- | --- | --- |
| Ethernet · MAC origen | 00:00:00:00:00:01 | 00:00:00:bb:bb:bb |
| Ethernet · MAC destino | 00:00:00:aa:aa:aa | 00:00:00:00:00:02 |
| IPv4 · origen | 200.0.0.1 | 200.0.0.1 |
| IPv4 · destino | 200.0.0.254 | 192.168.1.2 |
| TCP · puerto origen | 80 | 80 |
| TCP · puerto destino | 40000 | 50000 |
| TCP · flags relevantes | ACK | ACK |
| Datos TCP (primera línea si hay HTTP) | HTTP/1.1 200 OK | HTTP/1.1 200 OK |

El recorrido termina cuando h2 recibe la respuesta. Para este intercambio se supone que el GET y la respuesta caben en un segmento cada uno y que las dos reglas siguen vigentes.
