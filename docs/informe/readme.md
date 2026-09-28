## SUPUESTOS
Dado que UDP ya provee verificación de integridad (checksum), asumiremos que los paquetes que llegan a la capa de aplicación no están corruptos.

## DESICIONES 
No se acepta la subida de un archivo que ya esta subido en el servidor, por ejemplo no se puede subir un archivo de nombre ejemplo.txt si ya existe el ejemplo.txt en el almacenamiento del servidor.
Tampoco se puede subir un archivo de nombre ejemplo2.txt si ya se esta subiendo ese archivo por otro cliente. Esto evita casos donde 2 clientes intentan subir el mismo archivo al mismo tiempo.



## COMPLICACIONES (motivan desiciones)

No queremos fragmentacion, nos gustaria que un datagrama que mandamos sea igual a un datagrama que llega del otro lado (puede ser un supuesto) 
desicion -> para evitar fragmentacion (suponiendo que asi no ocurre) usamos un tamaño de datagramas (payload + header) < 1500 como por ejemplo 1400