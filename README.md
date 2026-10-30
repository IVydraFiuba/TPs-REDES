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

### Orden de ejecución recomendado

- Iniciar el controlador POX.
- Ejecutar la topología en Mininet.
- Verificar que el switch se conecte al controlador.

### Verificación básica

- Iniciar la red.
- Desde la CLI de Mininet:
    - Probar conectividad: `h2 ping h1`
