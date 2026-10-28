"""Erzeugt aus Spielplan, Resultaten und Tabelle die kleinen HTML-Stuecke,
die die Website beim Aufruf nachlaedt. Nur Python-Standardbibliothek."""
import html
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Europe/Zurich')
WT = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
WK = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
MO = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
WIR = 'Bösingen'
SPALTEN = [('rang', '#', 'Rang'), ('team', 'Team', 'Team'), ('sp', 'Sp', 'Spiele'), ('pkt', 'Pkt', 'Punkte'),
           ('w', 'S', 'Siege'), ('otw', 'SnV', 'Siege nach Verlängerung'), ('sow', 'SnP', 'Siege nach Penaltyschiessen'),
           ('sol', 'NnP', 'Niederlagen nach Penaltyschiessen'), ('otl', 'NnV', 'Niederlagen nach Verlängerung'),
           ('l', 'N', 'Niederlagen'), ('gf', 'TG', 'Erzielte Tore'), ('ga', 'TE', 'Erhaltene Tore'), ('diff', 'Diff', 'Tordifferenz')]


def e(s): return html.escape(str(s if s is not None else ''), quote=True)
def dt(g): return datetime.strptime(g['start'], '%Y-%m-%dT%H:%M')
def lang(d): return '%s, %d. %s %d' % (WT[d.weekday()], d.day, MO[d.month - 1], d.year)
def kurz(d): return '%s, %02d.%02d.%d' % (WK[d.weekday()], d.day, d.month, d.year)
def uhr(d): return d.strftime('%H:%M')
def ist_heim(g): return WIR in g['heim']
def hat_res(g): return g.get('tore_heim') is not None and g.get('tore_gast') is not None


def urteil(g):
    wir, die = (g['tore_heim'], g['tore_gast']) if ist_heim(g) else (g['tore_gast'], g['tore_heim'])
    return 'sieg' if wir > die else ('niederlage' if wir < die else 'remis')


def zeit_text(iso):
    try:
        return datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=ZoneInfo('UTC')).astimezone(TZ).strftime('%d.%m.%Y, %H:%M Uhr')
    except Exception:
        return ''


def spiel_zeile(g, jetzt):
    d = dt(g)
    h = '<b>%s</b>' % e(g['heim']) if ist_heim(g) else e(g['heim'])
    a = '<b>%s</b>' % e(g['gast']) if not ist_heim(g) else e(g['gast'])
    if hat_res(g):
        lab = {'sieg': '<small class="s">Sieg</small>', 'niederlage': '<small class="n">Niederlage</small>', 'remis': '<small class="n">Unentschieden</small>'}[urteil(g)]
        erg = '<div class="ergebnis">%d : %d%s</div>' % (g['tore_heim'], g['tore_gast'], lab)
    else:
        erg = '<div class="ergebnis offen">%s</div>' % ('Resultat folgt' if d < jetzt else 'offen')
    return '<li class="spiel%s"><div class="datum">%s<small>%s Uhr</small></div><div class="paar">%s &ndash; %s<span class="ort">%s</span></div>%s</li>' % (
        ' wir-heim' if ist_heim(g) else '', kurz(d), uhr(d), h, a, e(g.get('ort', '')), erg)


def spielbrett(sp, jetzt):
    gespielt = [g for g in sp if hat_res(g)]
    offen = [g for g in sp if not hat_res(g)]
    letztes = gespielt[-1] if gespielt else None
    naechstes = offen[0] if offen else None
    if letztes:
        d = dt(letztes); u = urteil(letztes)
        wh = ' wir' if ist_heim(letztes) else ''; wg = ' wir' if not ist_heim(letztes) else ''
        lab = {'sieg': 'Sieg', 'niederlage': 'Niederlage', 'remis': 'Unentschieden'}[u]
        links = '''<section aria-labelledby="b1"><h2 id="b1">Letztes Spiel</h2><p class="meta">%s, %s Uhr</p>
<div class="stand"><span class="team%s">%s</span><span class="tore%s">%d</span><span class="team%s">%s</span><span class="tore%s">%d</span></div>
<span class="urteil %s">%s</span></section>''' % (
            lang(d), uhr(d), wh, e(letztes['heim']), wh, letztes['tore_heim'], wg, e(letztes['gast']), wg, letztes['tore_gast'], u, lab)
    else:
        links = '<section aria-labelledby="b1"><h2 id="b1">Letztes Spiel</h2><p class="leer">Noch kein Resultat in dieser Saison.</p></section>'
    if naechstes:
        d = dt(naechstes)
        status = '' if d >= jetzt - timedelta(hours=1) else '<p class="wo">Resultat folgt, sobald es bei Swiss Icehockey eingetragen ist.</p>'
        rechts = '''<section class="naechstes" aria-labelledby="b2"><h2 id="b2">Nächstes Spiel</h2>
<p class="wann">%s</p><p class="uhr">%s Uhr</p><p class="paarung">%s &ndash; %s</p><p class="wo">%s</p>%s</section>''' % (
            lang(d), uhr(d), e(naechstes['heim']), e(naechstes['gast']), e(naechstes.get('ort', '')), status)
    else:
        rechts = '<section class="naechstes" aria-labelledby="b2"><h2 id="b2">Nächstes Spiel</h2><p class="leer">Der Spielplan der nächsten Saison folgt.</p></section>'
    return links + rechts, offen[:4]


def render(spiele, tabelle, conf, jetzt=None, status=None):
    """spiele/tabelle: Inhalt von spiele.json / tabelle.json; conf: sihf.json. Gibt {name: html} zurueck."""
    jetzt = jetzt or datetime.now(TZ).replace(tzinfo=None)
    status = status or {}
    sp = sorted(spiele.get('spiele', []), key=lambda g: g['start'])
    brett, kommende = spielbrett(sp, jetzt)
    n = ''.join(spiel_zeile(g, jetzt) for g in kommende)
    out, mon = '', None
    for g in sp:
        d = dt(g); m = (d.year, d.month)
        if m != mon:
            out += ('</ol>' if mon else '') + '<h2 class="monat">%s %d</h2><ol class="spiele">' % (MO[d.month - 1], d.year); mon = m
        out += spiel_zeile(g, jetzt)
    out += '</ol>' if mon else ''
    kopf = ''.join('<th scope="col" title="%s"%s>%s</th>' % (e(t), ' class="t"' if k == 'team' else '', e(h)) for k, h, t in SPALTEN)
    zeilen = ''
    for r in tabelle.get('zeilen', []):
        zeilen += '<tr%s>%s</tr>' % (' class="wir"' if WIR in r['team'] else '', ''.join(
            ('<th scope="row" class="t">%s</th>' if k == 'team' else '<td%s>%%s</td>' % (' class="pkt"' if k == 'pkt' else '')) % e(r.get(k, '')) for k, _, _ in SPALTEN))
    return {
        'brett': brett,
        'naechste': '<ol class="spiele">%s</ol>' % n if n else '<p>Der Spielplan der nächsten Saison folgt.</p>',
        'spielplan': out,
        'spielplan-quelle': 'Quelle: Swiss Icehockey. Zuletzt geprüft: %s. Massgebend ist der <a href="%s" target="_blank" rel="noopener noreferrer">offizielle Spielplan</a>.' % (
            e(zeit_text(status.get('spiele_geprueft') or spiele.get('aktualisiert', ''))), e(conf['spielplan_url'])),
        'tabelle': '<table class="tabelle"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (kopf, zeilen),
        'tabelle-quelle': 'Quelle: Swiss Icehockey. Zuletzt geprüft: %s. Massgebend ist die <a href="%s" target="_blank" rel="noopener noreferrer">offizielle Tabelle</a>.' % (
            e(zeit_text(status.get('tabelle_geprueft') or tabelle.get('aktualisiert', ''))), e(conf['tabelle_url'])),
    }
