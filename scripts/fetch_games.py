#!/usr/bin/env python3
"""Holt Spielplan (ICS) und Resultate (Spielplan-Seite) von Swiss Icehockey
und schreibt data/spiele.json. Nur Python-Standardbibliothek.

Aufruf:  python3 scripts/fetch_games.py            (holt online)
         python3 scripts/fetch_games.py --ics datei.ics --html seite.html   (offline/Test)
"""
import argparse, html, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import status
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'spiele.json')
CONF = json.load(open(os.path.join(ROOT, 'data', 'sihf.json'), encoding='utf-8'))
UA = 'EHC-Boesingen-Website/1.0 (Vereinsseite; Abruf alle paar Stunden; Kontakt: ' + CONF['kontakt_email'] + ')'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'de'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')


def parse_ics(text):
    text = re.sub(r'\r?\n[ \t]', '', text)  # gefaltete Zeilen
    games = []
    for blk in re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', text, flags=re.S):
        f = {}
        for line in blk.strip().splitlines():
            k, _, v = line.partition(':')
            f[k.split(';')[0]] = v.strip()
        m = re.match(r'(\d{4})(\d\d)(\d\d)T(\d\d)(\d\d)', f.get('DTSTART', ''))
        if not m:
            continue
        summ = f.get('SUMMARY', '')
        summ = re.sub(r'\s*\((\w+)\)\s*$', '', summ)
        if ' - ' not in summ:
            continue
        heim, gast = [s.strip() for s in summ.split(' - ', 1)]
        gid = re.search(r'(\d+)$', f.get('UID', ''))
        games.append({
            'id': gid.group(1) if gid else summ,
            'start': '%s-%s-%sT%s:%s' % m.groups(),
            'heim': heim, 'gast': gast,
            'ort': f.get('LOCATION', ''),
            'wettbewerb': re.sub(r'\s*\(\d{4}\)', '', re.sub(r'^\w+\s+\w+\s+', '', f.get('DESCRIPTION', ''))).replace('\\', ''),
            'tore_heim': None, 'tore_gast': None,
        })
    return games


def parse_results(page, games):
    """Sucht zu jedem Spiel den Link .../game/<id> und liest das Resultat aus dem Linktext."""
    found = 0
    for g in games:
        m = re.search(r'<a[^>]+href="[^"]*/game/\d*?%s"[^>]*>(.*?)</a>' % re.escape(g['id']), page, flags=re.S)
        if not m:
            continue
        txt = html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))
        txt = re.sub(r'\s+', ' ', txt)
        if 'Ende' not in txt:
            continue
        txt = txt.split('Ende', 1)[1]
        for name in sorted({g['heim'], g['gast']}, key=len, reverse=True):
            txt = txt.replace(name, ' ')
        nums = re.findall(r'\b\d{1,2}\b', txt)
        if len(nums) >= 2:
            g['tore_heim'], g['tore_gast'] = int(nums[0]), int(nums[1])
            found += 1
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ics'); ap.add_argument('--html')
    a = ap.parse_args()
    try:
        ics = open(a.ics, encoding='utf-8').read() if a.ics else get(CONF['ics_url'])
        games = parse_ics(ics)
        if not games:
            raise RuntimeError('Keine Spiele im Kalender gefunden')
    except Exception as e:
        print('FEHLER Kalender:', e, file=sys.stderr)
        sys.exit(1)  # alte spiele.json bleibt unveraendert

    # bereits bekannte Resultate behalten, falls die Seite einmal nicht erreichbar ist
    old = {}
    if os.path.exists(OUT):
        for g in json.load(open(OUT, encoding='utf-8')).get('spiele', []):
            old[g['id']] = g
    for g in games:
        o = old.get(g['id'])
        if o and o.get('tore_heim') is not None:
            g['tore_heim'], g['tore_gast'] = o['tore_heim'], o['tore_gast']
    try:
        page = open(a.html, encoding='utf-8').read() if a.html else get(CONF['spielplan_url'])
        n = parse_results(page, games)
        print('Resultate gelesen:', n)
    except Exception as e:
        print('WARNUNG Resultate:', e, file=sys.stderr)

    # manuelle Korrekturen/zusaetzliche Spiele (data/spiele_manuell.json) haben Vorrang
    man = os.path.join(ROOT, 'data', 'spiele_manuell.json')
    if os.path.exists(man):
        extra = {g['id']: g for g in json.load(open(man, encoding='utf-8')).get('spiele', [])}
        games = [extra.pop(g['id'], g) for g in games] + list(extra.values())

    games.sort(key=lambda g: g['start'])
    status.stempel('spiele_geprueft')
    data = {'aktualisiert': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'spiele': games}
    new = json.dumps(data, ensure_ascii=False, indent=1)
    # nur schreiben, wenn sich inhaltlich etwas geaendert hat (vermeidet unnoetige Neu-Veroeffentlichungen)
    if os.path.exists(OUT):
        prev = json.load(open(OUT, encoding='utf-8'))
        if prev.get('spiele') == games:
            print('Keine Aenderung')
            return
    open(OUT, 'w', encoding='utf-8').write(new)
    print('Geschrieben:', len(games), 'Spiele')


if __name__ == '__main__':
    main()
