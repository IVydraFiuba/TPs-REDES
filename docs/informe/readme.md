## SUPUESTOS
Dado que UDP ya provee verificación de integridad (checksum), asumiremos que los paquetes que llegan a la capa de aplicación no están corruptos.

## DESICIONES 

## COMPLICACIONES (motivan desiciones)

No queremos fragmentacion, nos gustaria que un datagrama que mandamos sea igual a un datagrama que llega del otro lado (puede ser un supuesto) 
desicion -> para evitar fragmentacion (suponiendo que asi no ocurre) usamos un tamaño de datagramas (payload + header) < 1500 como por ejemplo 1400