#!/usr/bin/env python3
"""Holt die Tabelle von Swiss Icehockey und schreibt data/tabelle.json.
Nur Python-Standardbibliothek. Bei Fehlern bleibt die alte Datei unveraendert.
Aufruf: python3 scripts/fetch_table.py [--html seite.html]"""
import argparse, html, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import status
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'tabelle.json')
CONF = json.load(open(os.path.join(ROOT, 'data', 'sihf.json'), encoding='utf-8'))
UA = 'EHC-Boesingen-Website/1.0 (Vereinsseite; Abruf alle paar Stunden; Kontakt: ' + CONF['kontakt_email'] + ')'
KEYS = ['rang', 'team', 'sp', 'pkt', 'ppsp', 'w', 'otw', 'sow', 'sol', 'otl', 'l', 'gf', 'ga', 'diff', 'serie']


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'de'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')


def text(s):
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    s = re.sub(r'<img[^>]*\balt="([^"]*)"[^>]*>', r' \1 ', s)  # Logo-Alt-Text mitnehmen
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def team_name(t):
    t = re.sub(r'\s*\([^)]*\)\s*', ' ', t).strip()
    w = t.split()
    changed = True
    while changed:                          # "X Y X Y" -> "X Y" (Name steht oft mehrfach)
        changed = False
        for k in range(1, len(w) // 2 + 1):
            if w[:k] == w[k:2 * k]:
                w = w[:k] + w[2 * k:]
                changed = True
                break
    if len(w) > 1 and w[-1].isupper() and len(w[-1]) >= 3:   # Kuerzel am Ende entfernen
        w = w[:-1]
    return ' '.join(w)


def parse(page):
    rows = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', page, flags=re.S):
        cells = [text(c) for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, flags=re.S)]
        if len(cells) < 14 or not re.fullmatch(r'\d{1,2}', cells[0]):
            continue
        cells += [''] * (len(KEYS) - len(cells))
        d = dict(zip(KEYS, cells[:len(KEYS)]))
        d['team'] = team_name(d['team'])
        rows.append(d)
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--html'); ap.add_argument('--out')
    a = ap.parse_args()
    out = a.out or OUT
    try:
        page = open(a.html, encoding='utf-8').read() if a.html else get(CONF['tabelle_url'])
        rows = parse(page)
        if len(rows) < 2:
            raise RuntimeError('Keine Tabellenzeilen gefunden (Aufbau der Seite geaendert?)')
    except Exception as e:
        print('FEHLER Tabelle:', e, file=sys.stderr)
        sys.exit(1)
    if not a.out:
        status.stempel('tabelle_geprueft')
    prev = json.load(open(out, encoding='utf-8')) if os.path.exists(out) else {}
    if prev.get('zeilen') == rows:
        print('Keine Aenderung'); return
    json.dump({'aktualisiert': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'zeilen': rows},
              open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Geschrieben:', len(rows), 'Zeilen')


if __name__ == '__main__':
    main()
