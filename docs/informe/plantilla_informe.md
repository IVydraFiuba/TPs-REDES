# Informe de Trabajo Práctico: Protocolos de Comunicación

**Despues lo pasamos a PDF**

---

## 1. Introducción
[Describir brevemente el objetivo del trabajo práctico, el contexto del problema a resolver y un resumen de lo que se presentará en el informe.]

---

## 2. Hipótesis y suposiciones realizadas
[Enumerar y justificar cualquier suposición técnica o de diseño que se haya tomado durante el desarrollo. Por ejemplo, suposiciones sobre el entorno de red, el tamaño máximo de los paquetes, el comportamiento del usuario, etc.]

* Suposición 1: [Descripción]
* Suposición 2: [Descripción]

---

## 3. Implementación

### 3.1 Arquitectura de la Aplicación
[Describir la arquitectura general de la aplicación desarrollada. Detallar cómo interactúan las distintas partes.]

### 3.2 Uso de la Interfaz de Sockets
[Demostrar el conocimiento sobre la API de sockets utilizada. Explicar cómo se configuran, cómo se envían/reciben datos y cómo se manejan los timeouts o bloqueos.]

### 3.3 Protocolos implementados (capas de transporte y capad de aplicacion) 
[Detallar el protocolo diseñado para cada una de las operaciones requeridas (conexión, transferencia de datos, desconexión, etc.). Se puede usar un diagrama de estados o un flujo de mensajes.]

---

## 4. Pruebas y Análisis

### 4.1 Resultados de Ejecuciones de Prueba
[Adjuntar capturas de pantalla de la ejecución del cliente y fragmentos relevantes de los logs del servidor para demostrar que el sistema funciona correctamente en casos base.]

*   **Captura del Cliente:** 
    *(Insertar imagen: `![Ejecución Cliente](ruta/a/imagen.png)`)*
*   **Logs del Servidor:**
    ```text
    [Pegar aquí fragmentos del log del servidor]
    ```

### 4.2 Análisis Comparativo: Stop&Wait vs SACK
Se comparó el tiempo necesario para enviar archivos y el *throughput* promedio utilizando archivos de distintos tamaños y bajo distintas configuraciones de pérdida de paquetes.

**Archivos utilizados:**
1. Archivo Pequeño: [Ej: 100 KB]
2. Archivo Mediano: [Ej: 1 MB]
3. Archivo Grande: [Ej: 10 MB]

#### Resultados con 0% de Pérdida de Paquetes
| Tamaño de Archivo | Tiempo Stop&Wait | Tiempo SACK | Throughput Stop&Wait | Throughput SACK |
| :--- | :--- | :--- | :--- | :--- |
| Pequeño | [Tiempo] | [Tiempo] | [Valor] bps | [Valor] bps |
| Mediano | [Tiempo] | [Tiempo] | [Valor] bps | [Valor] bps |
| Grande | [Tiempo] | [Tiempo] | [Valor] bps | [Valor] bps |

#### Resultados con [X]% de Pérdida de Paquetes
| Tamaño de Archivo | Tiempo Stop&Wait | Tiempo SACK | Throughput Stop&Wait | Throughput SACK |
| :--- | :--- | :--- | :--- | :--- |
| Pequeño | [Tiempo] | [Tiempo] | [Valor] bps | [Valor] bps |
| Mediano | [Tiempo] | [Tiempo] | [Valor] bps | [Valor] bps |
| Grande | [Tiempo] | [Tiempo] | [Valor] bps | [Valor] bps |

#### Resultados con [Y]% de Pérdida de Paquetes
| Tamaño de Archivo | Tiempo Stop&Wait | Tiempo SACK | Throughput Stop&Wait | Throughput SACK |
| :--- | :--- | :--- | :--- | :--- |
| Pequeño | [Tiempo] | [Tiempo] | [Valor] bps | [Valor] bps |
| Mediano | [Tiempo] | [Tiempo] | [Valor] bps | [Valor] bps |
| Grande | [Tiempo] | [Tiempo] | [Valor] bps | [Valor] bps |

**Observaciones del Análisis:**
[Escribir aquí las conclusiones obtenidas a partir de las tablas. ¿Cómo afecta el tamaño del archivo? ¿Cómo degrada el rendimiento el porcentaje de pérdida en cada protocolo?]

---

## 5. Preguntas a responder

**1. Describa la arquitectura Cliente-Servidor.**
[Tu respuesta aquí]

**2. ¿Cuál es la función de un protocolo de capa de aplicación?**
[Tu respuesta aquí]

**3. Detalle el protocolo de aplicación desarrollado en este trabajo.**
[Tu respuesta aquí. Puede referenciar a la sección 3.3 si ya fue detallado exhaustivamente, o agregar los detalles semánticos de los mensajes de aplicación aquí]

**4. La capa de transporte del stack TCP/IP ofrece dos protocolos: TCP y UDP. ¿Qué servicios proveen dichos protocolos? ¿Cuáles son sus características? ¿Cuándo es apropiado utilizar cada uno?**
[Tu respuesta aquí]

**5. Justifique si el protocolo desarrollado cuenta con mecanismos de control de congestión, en caso de tenerlos, descríbalos.**
[Tu respuesta aquí. Considerar si implementaron ventanas dinámicas, slow start, congestion avoidance, o si al ser Stop&Wait / SACK básico con ventana fija carece de control de congestión real en la red]

**6. ¿Cuál de los dos protocolos desarrollados envía archivos en la menor cantidad de tiempo? ¿Es siempre el mismo?**
[Tu respuesta aquí, referenciando los resultados obtenidos en la sección 4.2]

---

## 6. Dificultades encontradas
[Mencionar los problemas que surgieron durante la codificación, pruebas o diseño del protocolo (ej. manejo de timers, cálculo del RTT, corrupción de archivos, problemas de sincronización) y cómo fueron solucionados.]

---

## 7. Conclusión
[Cierre del informe. Resumir los aprendizajes más importantes, evaluar si se cumplieron los objetivos iniciales y realizar una reflexión final sobre las diferencias reales de rendimiento entre Stop&Wait y SACK comprobadas empíricamente.]