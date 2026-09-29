# Arquitectura y supuestos

Este documento registra simplificaciones adoptadas para mantener la
implementación dentro del alcance del trabajo práctico.

## Identificación de sesiones UDP

El servidor identifica una sesión por el par `(IP, puerto)` del cliente. Los
segmentos RDT no incluyen un identificador de sesión adicional.

Esta decisión se apoya en los siguientes supuestos:

- Cada ejecución de `upload.py` o `download.py` crea su propio socket UDP.
- Un socket cliente mantiene como máximo una sesión activa.
- Un cliente no ejecuta transferencias concurrentes sobre el mismo socket.
- La IP y el puerto del cliente no cambian durante una transferencia.
- Un `SYN` de un endpoint con una sesión activa se considera una retransmisión.
- No llegan datagramas demorados después de finalizar su sesión.
- No se reutiliza un puerto mientras queden datagramas de su sesión anterior.

Estas restricciones permiten que el despachador futuro use `(IP, puerto)` como
clave del registro de sesiones. Stop-and-Wait y SACK mantendrán sus números de
secuencia y confirmación dentro del canal asociado a ese endpoint.
