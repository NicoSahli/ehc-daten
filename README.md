# ehc-daten

Holt alle 2 Stunden Spielplan, Resultate und Tabelle von Swiss Icehockey und legt sie hier ab.
Die Vereinswebsite lädt diese Dateien beim Aufruf nach. Hier liegen nur öffentliche Spieldaten.

- `data/`      Rohdaten (`spiele.json`, `tabelle.json`) und Einstellungen (`sihf.json`)
- `fragmente/` fertige Anzeige-Stücke für die Website
- `scripts/`   die Skripte
- Von Hand ein Spiel ergänzen oder korrigieren: Datei `data/spiele_manuell.json` anlegen, Beispiel:
  `{"spiele": [{"id": "x1", "start": "2026-09-05T18:00", "heim": "A", "gast": "B", "ort": "Halle", "wettbewerb": "Freundschaftsspiel", "tore_heim": 3, "tore_gast": 2}]}`
- Sofort aktualisieren: Reiter «Actions», «Daten aktualisieren», «Run workflow».
