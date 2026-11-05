#!/usr/bin/env python3
"""Genera diagramas SVG y PNG con Graphviz usando topo_config.json."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate():
    config = json.loads((ROOT / 'topo_config.json').read_text())
    output = ROOT / 'docs' / 'informe' / 'img'
    output.mkdir(parents=True, exist_ok=True)
    def quote(value):
        return json.dumps(value, ensure_ascii=False)
    lines = [
        'graph topologia {',
        '  graph [rankdir=LR, bgcolor="white", pad=0.3, nodesep=0.6, ranksep=1.0, fontname="DejaVu Sans"];',
        '  node [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=11, margin=0.18];',
        '  edge [fontname="DejaVu Sans", fontsize=10, color="#64748b"];',
        '  label="Topología SDN · redes pública y privada";',
        '  labelloc=t;',
        '  controller [label="Controlador POX", fillcolor="#ede9fe"];',
    ]
    gateways = config['gateways']
    label = config['switch'] + '\nSwitch OpenFlow 1.0'
    for network, title in [('public', 'Pública'), ('private', 'Privada')]:
        gateway = gateways[network]
        label += f'\n\n{title}: {gateway["ip"]}\nMAC: {gateway["mac"]}'
    lines.append(f'  switch [label={quote(label)}, fillcolor="#e2e8f0"];')
    lines.append('  controller -- switch [style=dashed, label="OpenFlow", color="#7c3aed"];')
    for host in config['hosts']:
        gateway = gateways[host['network']]['ip'].split('/')[0]
        label = f'{host["name"]}\nIP: {host["ip"]}\nMAC: {host["mac"]}\nGateway: {gateway}'
        color = '#dbeafe' if host['network'] == 'public' else '#dcfce7'
        lines.append(f'  {quote(host["name"])} [label={quote(label)}, fillcolor="{color}"];')
        start, end = (quote(host['name']), 'switch') if host['network'] == 'public' else ('switch', quote(host['name']))
        lines.append(f'  {start} -- {end} [label="Puerto {host["switch_port"]}"];')
    lines.append('}')
    source = output / 'topologia.dot'
    source.write_text('\n'.join(lines) + '\n')
    for extension in ('svg', 'png'):
        subprocess.run(['dot', f'-T{extension}', str(source), '-o', str(output / f'topologia.{extension}')], check=True)
    print(f'Diagramas generados en {output}')


if __name__ == '__main__':
    generate()
