# REWE eBons extrahieren

Diese Anleitung beschreibt, wie du mit dem aktuellen Stand des Projekts deine REWE-eBons herunterladen, als PDFs entpacken und anschließend in die gemeinsame JSON-Datenbasis importieren kannst.

> Status: **funktionierender Workflow**
>
> Der Download der REWE-eBons als ZIP wurde im Projekt erfolgreich getestet. Die ZIP-Datei wird heruntergeladen, automatisch nach PDF-Dateien entpackt und anschließend in den REWE-Importpfad übernommen.

---

## Was der aktuelle Stand kann

Der aktuelle REWE-Workflow kann:

- REWE-Cookies aus einer Datei laden
- REWE-Cookies interaktiv aus einem laufenden Browser-Kontext uebernehmen
- die `customerId` serverseitig aus der aktiven Session ermitteln
- die Session gegen den REWE-ZIP-Endpunkt prüfen
- alle eBons als ZIP herunterladen
- die ZIP automatisch in PDF-Dateien entpacken
- bei `update` aus bereits vorhandenen PDFs nur neue eBons anhand bereits bekannter REWE-IDs importieren
- die PDFs direkt in `rewe_receipts.json` importieren

Der aktuelle Workflow kann noch **nicht automatisch**:

- REWE-Daten bereits vollständig mit Lidl-Daten harmonisieren

---

## Voraussetzungen

Du brauchst:

- Python 3
- installierte Projekt-Abhängigkeiten
- ein eingeloggtes REWE-Konto im Browser
- entweder ein lokales Browserprofil mit aktiver REWE-Session oder eine exportierte Cookie-Datei
- optional deine REWE-`customerId` als Fallback

Abhängigkeiten installieren:

```bash
pip install -r requirements.txt
```

---

## Schritt 1: Bei REWE im Browser anmelden

Öffne REWE im Browser und melde dich in deinem Konto an.

Relevante Seite:

- `https://www.rewe.de/shop/mydata/meine-einkaeufe/im-markt`

Wichtig:

- Lass den Browser geöffnet.
- Führe den Export möglichst direkt nach dem Login aus.
- Frische Cookies funktionieren zuverlässiger als ältere Exporte.

---

## Schritt 2: Session bereitstellen

Es gibt zwei praktikable Wege:

1. **empfohlen:** eine exportierte Cookie-/Request-Datei per `--cookies-file`
2. **alternativ:** ein lokales Browserprofil per `--browser`

### Alternative: Direkt aus dem Browserprofil lesen

Der Workflow kann REWE-Cookies direkt aus deinem lokalen Browserprofil lesen.

Unterstützte Browser:

- `firefox`
- `librewolf`
- `chrome`
- `chromium`

Beispiel:

```bash
python3 get_data.py initial --retailer rewe --browser firefox
```

Das ist ein optionaler Best-Effort-Pfad.

> Hinweis:
> Die Browser-Profil-Extraktion ist ein Best-Effort-Pfad. Je nach Browser, Profil und Betriebssystem koennen wichtige Session-Cookies lokal fehlen. In realen Tests mit Firefox fehlte z. B. `rstp`, sodass der REWE-Abruf dann weiter per `--cookies-file` erfolgen muss.
> Das kann auch dann passieren, wenn `rstp` im Browser-UI sichtbar ist: sichtbar im Browser bedeutet hier nicht automatisch, dass das Cookie im lokalen Profil (`cookies.sqlite` / Recovery-Store) fuer externe Tools auslesbar persistiert wurde.

### Empfohlener Weg: Cookies aus Datei exportieren

Der Check-/Import-Pfad unterstützt mehrere Formate:

- JSON-Export von Cookie-Erweiterungen
- Netscape-Cookie-Datei
- roher `Cookie:`-Header aus den DevTools
- einfache `name=value`-Paare
- sogar ein kompletter kopierter Request-Header, solange eine `Cookie:`-Zeile enthalten ist

Am einfachsten ist ein JSON-Export, z. B. in eine Datei wie:

- `rewe_test_cookies.json`
- `rewe_cookies.json`

Wichtige Cookies, die typischerweise enthalten sein sollten:

- `rstp`
- `_rdfa`
- `mtc`

Zusätzliche Cookies wie `cf_clearance`, `__cf_bm`, `_cfuvid`, `consentSettings`, `websitebot-launch` und `MRefererUrl` koennen vorhanden sein, sind nach aktuellem Stand aber nicht die zentralen Erfolgsfaktoren.

Vor dem eigentlichen Abruf kannst du die Datei jetzt mit einem Diagnosebefehl pruefen:

```bash
python3 get_data.py check --retailer rewe --cookies-file rewe_test_cookies.json
```

Der Diagnosebefehl meldet dir u. a.:

- ob `rstp` vorhanden ist
- ob hilfreiche REWE-Zusatzcookies fehlen
- ob eine `customerId` bereits direkt in der Datei enthalten ist

Zusätzlich bekommst du jetzt einen Ampelstatus:

- `GRUEN`: Datei wirkt direkt nutzbar
- `GELB`: Datei ist brauchbar, aber es fehlen noch hilfreiche Zusatzcookies
- `ROT`: Datei ist wahrscheinlich nicht ausreichend

---

## Schritt 3: `customerId`-Auflösung

Der aktuelle Workflow versucht die REWE-`customerId` automatisch in dieser Reihenfolge zu ermitteln:

1. explizit über `--customer-id`
2. serverseitig aus der aktiven REWE-Session über `https://www.rewe.de/shop/mydata/couponwallet`
3. aus der Eingabedatei, wenn dort ein kompletter Request oder `customerId=...` enthalten ist
4. aus dem lokalen Cache in `tmp/rewe/customer_id.txt`

Empfohlener produktiver Standardpfad:

```bash
python3 get_data.py check --retailer rewe --cookies-file rewe_test_cookies.json
python3 get_data.py initial --retailer rewe --cookies-file rewe_test_cookies.json
```

Alternative Browserprofil-Pfade gibt es zwar weiterhin, aber sie sind weniger verlässlich. Browserprofil-Pfad:

```bash
python3 get_data.py initial --retailer rewe --browser firefox
```

Wenn der Browserprofil-Pfad `rstp` nicht liefern kann, wechsle bitte auf den weiterhin empfohlenen Datei-Pfad.

Der weiterhin empfohlene Datei-Pfad ist:

```bash
python3 get_data.py initial --retailer rewe --cookies-file rewe_test_cookies.json
```

Falls die Session-basierte Ermittlung nicht greift, kannst du die `customerId` weiterhin manuell übergeben.

Am einfachsten findest du sie in den Browser-DevTools:

1. Öffne die Seite `Meine Einkäufe im Markt`
2. Öffne die DevTools (`F12` oder Browser-Menü)
3. Gehe zum Tab **Network**
4. Suche nach dem Request:
   - `GET /api/receipts/zip?customerId=...`
5. Kopiere den Wert hinter `customerId=`

Beispiel:

```text
/api/receipts/zip?customerId=12345678-1234-1234-1234-123456789abc
```

Dann ist die `customerId`:

```text
12345678-1234-1234-1234-123456789abc
```

### Hinweis zu reinen Cookie-Dateien

Wenn du eine reine Cookie-Datei verwendest, ist die `customerId` dort meist **nicht** direkt enthalten. Das ist jetzt unkritisch, solange der `couponwallet`-Endpunkt mit deiner Session erreichbar ist.

---

## Schritt 4: REWE-eBons herunterladen und importieren

Im Projektordner bevorzugt ausführbar:

```bash
python3 get_data.py check --retailer rewe --cookies-file rewe_test_cookies.json
python3 get_data.py initial --retailer rewe --cookies-file rewe_test_cookies.json
```

Beispiel:

```bash
python3 get_data.py initial --retailer rewe --cookies-file rewe_test_cookies.json --customer-id 12345678-1234-1234-1234-123456789abc
```

Oft reicht inzwischen bereits ohne `--customer-id`:

```bash
python3 get_data.py initial --retailer rewe --cookies-file rewe_test_cookies.json
```

Für spätere Läufe kannst du auch `update` verwenden:

```bash
python3 get_data.py update --retailer rewe --output-dir tmp/rewe
```

Wichtig: REWE bietet aktuell keinen echten serverseitigen Delta-Endpunkt. `update` arbeitet deshalb rein lokal auf bereits vorhandenen PDFs in `tmp/rewe/pdfs` (bzw. im gewählten `--output-dir`) und importiert diese erneut per Upsert in den konfigurierten Store. Bereits bekannte Bons werden also nicht vorab ausgesiebt, sondern beim Persistieren aktualisiert bzw. unverändert belassen.

Optional kannst du ein anderes Ausgabeverzeichnis setzen:

```bash
python3 get_data.py initial --retailer rewe --cookies-file rewe_test_cookies.json --output-dir tmp/rewe_export
```

---

## Ausgabe

Standardmäßig erzeugt der Workflow folgende Dateien und Ordner:

- `tmp/rewe/receipts.zip`
- `tmp/rewe/pdfs/`
- `rewe_receipts.json`

In `tmp/rewe/pdfs/` liegen anschließend alle entpackten eBon-PDFs.

---

## Was du bei Erfolg sehen solltest

Typische erfolgreiche Ausgabe:

```text
Teste REWE-Session...
✓ REWE-Session erfolgreich getestet
✓ REWE-eBons ZIP gespeichert: tmp/rewe/receipts.zip
✓ REWE-eBons entpackt nach: tmp/rewe/pdfs
✓ REWE-eBons importiert: ...
```

---

## Fehlersuche

### `401 Unauthorized`

Bedeutung:
- Die Session ist ungültig oder abgelaufen.

Lösung:
- bei REWE erneut einloggen
- Cookies neu exportieren
- Workflow direkt danach erneut starten

### `403 Forbidden`

Bedeutung:
- REWE/Cloudflare akzeptiert die Session nicht.

Mögliche Ursachen:
- `cf_clearance` fehlt
- `__cf_bm` fehlt
- Cookies sind veraltet
- `customerId` gehört nicht zur aktuellen Session

Lösung:
- Browser geöffnet lassen
- Seite `Meine Einkäufe im Markt` erneut laden
- Cookies frisch exportieren
- sicherstellen, dass `rstp`, `_rdfa`, `cf_clearance` und `__cf_bm` enthalten sind

### `404`

Bedeutung:
- `customerId` ist falsch oder nicht mehr gültig.

Lösung:
- `customerId` in den DevTools erneut prüfen

### `429 Too Many Requests`

Bedeutung:
- REWE blockiert zu viele Anfragen in kurzer Zeit.

Lösung:
- einige Minuten warten
- danach erneut versuchen

---

## Sicherheitshinweise

Cookie-Dateien enthalten sensible Authentifizierungsdaten.

Bitte beachte:

- Cookie-Dateien niemals committen
- Cookie-Dateien niemals weitergeben
- Cookie-Dateien lokal sicher speichern
- Cookie-Dateien nach erfolgreichem Download wieder löschen, wenn du sie nicht mehr brauchst

Die Dateien `rewe_cookies.json` und `tmp/` sind im Projekt bereits für Git ignoriert.

---

## Bekannte Grenzen des aktuellen Workflows

- REWE-Cookies können kurzlebig sein
- Cloudflare/WAF kann gelegentlich trotz korrekter Cookies blockieren
- die Session-basierte `customerId`-Ermittlung kann bei abgelaufenen oder von WAF geblockten Cookies fehlschlagen
- Browserprofil-Auslese ist ein Best-Effort-Pfad und kann wichtige Cookies wie `rstp` verpassen
- es gibt aktuell keinen echten serverseitigen inkrementellen Delta-Endpunkt für REWE; das Update arbeitet lokal über bereits vorhandene PDFs und reimportiert sie per Upsert in den Ziel-Store

---

## Kurzfassung

Wenn du schnell starten willst:

1. Bei REWE einloggen
2. Cookies exportieren
3. Diesen Befehl ausführen:

```bash
python3 get_data.py initial --retailer rewe --cookies-file rewe_test_cookies.json
```

Wenn nötig, ergänze als Fallback:

```bash
python3 get_data.py initial --retailer rewe --cookies-file rewe_test_cookies.json --customer-id <REWE_CUSTOMER_ID>
```

Danach findest du die PDFs in:

```text
tmp/rewe/pdfs/
```

Die importierten Daten landen zusätzlich in:

```text
rewe_receipts.json
```

