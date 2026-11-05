# TA-048 Redes - Trabajo Práctico 2: SDN / NAT

## Entorno de Trabajo y Ejecución

### Requisitos

- Python 3
- Mininet
- POX controller



### Organización de archivos


```text
TPs-REDES/
├── topo.py                  # Topología de Mininet del TP
├── pox/
│   ├── pox.py               # Lanzador de POX
│   └── ext/
│       └── protorouter.py   # Controlador del TP
└── docs/
```

### Topología actual

![Topología actual](docs/informe/img/topologia.png)

Para regenerar el diagrama después de modificar la configuración, instalar
Graphviz (comando `dot`) y ejecutar desde la raíz del repositorio:

```bash
python3 tools/generar_topologia.py
```
Se generan el archivo fuente DOT, un SVG y un PNG en `docs/informe/img/`.


### Ejecución del controlador

Desde una terminal, ejecutar:
```bash
python3 pox/pox.py log.level --DEBUG protorouter
```

### Ejecución de la topología

En otra terminal, ejecutar:
```bash
sudo python3 topo.py
```
