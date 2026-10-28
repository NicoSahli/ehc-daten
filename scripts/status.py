"""Merkt sich, wann die Daten zuletzt erfolgreich bei Swiss Icehockey abgeholt wurden (auch ohne Aenderung)."""
import json, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PFAD = os.path.join(ROOT, 'data', 'status.json')


def lesen():
    try:
        return json.load(open(PFAD, encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def stempel(name):
    d = lesen()
    d[name] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    json.dump(d, open(PFAD, 'w', encoding='utf-8'), indent=1)
