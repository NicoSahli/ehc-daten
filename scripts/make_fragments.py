#!/usr/bin/env python3
"""Schreibt fragmente/*.html aus data/spiele.json, data/tabelle.json und data/sihf.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fragmente, status

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd = lambda n: json.load(open(os.path.join(ROOT, 'data', n + '.json'), encoding='utf-8'))
os.makedirs(os.path.join(ROOT, 'fragmente'), exist_ok=True)
teile = fragmente.render(rd('spiele'), rd('tabelle'), rd('sihf'), status=status.lesen())
for name, inhalt in teile.items():
    p = os.path.join(ROOT, 'fragmente', name + '.html')
    if os.path.exists(p) and open(p, encoding='utf-8').read() == inhalt:
        continue
    open(p, 'w', encoding='utf-8').write(inhalt)
    print('Geschrieben:', name)
print('Fertig')
