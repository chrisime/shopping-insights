# dm eBons extrahieren

Diese Anleitung beschreibt, wie du mit dem aktuellen Stand des Projekts deine dm-Kaufhistorie (Markt-eBons) abrufen und anschließend in die gemeinsame SQLite-Datenbasis importieren kannst.

> Status: **funktionierender Workflow**
>
> Der Abruf der dm-Kaufhistorie wurde im Projekt erfolgreich getestet. Die eBon-Details (JSON) und optional die Original-PDFs werden heruntergeladen und über den gemeinsamen Importpfad in `shopping_receipts.sqlite` übernommen.

---

## Was der aktuelle Stand kann

Der aktuelle dm-Workflow kann:

- dm-Session-Cookies aus einer Datei laden
- dm-Session-Cookies interaktiv aus einem laufenden Browser-Kontext übernehmen
- über den OAuth-2.0-Flow (PKCE) gegen `signin.dm.de` einen kurzfristigen Access-Token ausstellen
- die Session gegen den dm-Kaufhistorie-Endpunkt prüfen
- alle Seiten der Kaufhistorie abrufen (Cursor-Pagination)
- nur **Markt-eBons** als Belege importieren; Online-Bestellungen werden erkannt und separat ausgewiesen, aber nicht persistiert
- für jeden eBon die Detail-Daten (Datum, Filiale, Kasse, Rabatt, Payback-Punkte, DAN-Artikel) als JSON ablegen
- die Original-PDFs herunterladen und daraus die **Artikel (Name, Preis, Menge)** extrahieren – die dm-API selbst liefert nur Artikelnummern (DAN) ohne Namen/Preise
- bei `update` aus bereits vorhandenen eBon-JSONs nur neue Bons anhand bereits bekannter dm-IDs importieren
- die eBons direkt in `shopping_receipts.sqlite` importieren

Intern laufen Parse, Validierung und Persistenz über die gemeinsame Pipeline in `workflows/pipeline_runner.py`.

---

## Voraussetzungen

Du brauchst:

- Python 3
- installierte Projekt-Abhängigkeiten
- ein eingeloggtes dm-Konto im Browser (`account.dm.de/purchases`)
- entweder ein lokales Browserprofil mit aktiver dm-Session oder eine exportierte Cookie-Datei

Abhängigkeiten installieren:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Cookies für den OAuth-Flow exportieren

dm authentifiziert sich über einen OAuth-2.0-Flow mit PKCE. Die exportierte Cookie-Datei muss **mindestens die dm-Session-Cookies** enthalten, damit ein kurzfristiger Access-Token erstellt werden kann. Ohne eine gültige dm-Session ist kein Abruf möglich.

Benötigt werden insbesondere:

- Session-Cookies auf `signin.dm.de` (z. B. `_sessionid`, `sessionid`)
- das dm-SSO-Session-Cookie `_SI_SID_*` auf `.dm.de`
- hilfreiche Zusatzcookies (optional): `_SI_DID_*`, `_SI_VID_*`, `_dyjsession`, `_dyid_server`

Exportiere die Cookies direkt nach einem funktionierenden Aufruf von `https://account.dm.de/purchases` (z. B. mit einer Cookie-Editor-Erweiterung, JSON-Format) und speichere sie z. B. als `dm_cookies.json`.

Du kannst die Qualität der Cookie-Datei vorab prüfen:

```bash
python fetch_tickets.py check --retailer dm --cookies-file dm_cookies.json
```

Dieser Befehl zeigt eine Ampel-Diagnose und versucht, über die Session einen Access-Token auszustellen.

---

## Initialer Import

```bash
python fetch_tickets.py initial --retailer dm --cookies-file dm_cookies.json
```

Optional kannst du einen Ausgabeordner angeben:

```bash
python fetch_tickets.py initial --retailer dm --cookies-file dm_cookies.json --output-dir tmp/dm
```

Der Ablauf:

1. Access-Token über den OAuth-Flow ausstellen
2. dm-Session gegen den Kaufhistorie-Endpunkt prüfen
3. alle Seiten der Kaufhistorie abrufen
4. Markt-eBons identifizieren; Online-Bestellungen separat ausweisen
5. eBon-Details (JSON) und PDFs nach `tmp/dm/ebons/` bzw. `tmp/dm/pdf/` herunterladen
6. die eBons über die gemeinsame Pipeline importieren

---

## Update

Der Update-Modus importiert nur bereits lokal vorhandene eBon-JSONs neu (ohne erneuten Download):

```bash
python fetch_tickets.py update --retailer dm --output-dir tmp/dm
```

---

## Export

Aus dem aktuellen DB-Stand kannst du die dm-eBons als JSON exportieren:

```bash
python fetch_tickets.py export --retailer dm --output-file dm_receipts.json
```

---

## Wichtige Hinweise

- dm-Access-Tokens laufen nach ca. 2,5 Minuten ab. Der Client stellt bei Bedarf über die Session automatisch einen neuen Token aus und wiederholt den Request einmal.
- Es werden nur **Markt-eBons** als Belege importiert. Online-Bestellungen erscheinen in der Statistik des Laufs, werden aber nicht als Bons gespeichert.
- Cookie- und Request-Dateien enthalten sensible Authentifizierungsdaten – niemals committen, lokal sicher aufbewahren und nach Möglichkeit wieder löschen.
