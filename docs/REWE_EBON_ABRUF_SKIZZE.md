# Skizze: Abholen von REWE eBons

## Ziel
Dieses Dokument skizziert einen robusten Weg, REWE-eBons automatisiert abzuholen und in die bestehende Architektur von `shopping-analyzer` zu integrieren.

## Scope
- Technischer Abruf von eBons aus dem REWE-Webkonto
- Nutzung bestehender Browser-Session/Cookies (analog zum Lidl-Ansatz)
- Batch-Download via ZIP und Fallback auf Einzel-PDFs
- Fehler- und Risikobehandlung (Session-Ablauf, WAF, Rate Limits)

## Nicht-Ziele
- Umgehung von Schutzmechanismen
- Dauerhaft headless-bot-fester Zugriff ohne Browser-Session
- Rechtliche Bewertung (ToS/Compliance)

---

## Verifizierte Endpunkte

### 1) Einzelbon als PDF
- `GET /api/receipts/{receiptId}/pdf`
- Beispiel: `/api/receipts/41205d80-0699-39c2-b410-4d355438d845/pdf`
- Erwartete Antwort:
  - `200 OK`
  - `content-type: application/pdf`
  - `content-disposition: attachment; filename="Dein REWE eBon vom ...pdf"`

### 2) Alle Bons als ZIP
- `GET /api/receipts/zip?customerId={customerId}`
- Beispiel: `/api/receipts/zip?customerId=c8a8bb0a-7215-42fa-a988-465a95e7f663`
- Erwartete Antwort:
  - `200 OK`
  - `content-type: application/zip`
  - `content-disposition: attachment; filename="Deine REWE eBons.zip"`

### Einordnung
- Diese Endpunkte sind fachlich direkt relevant.
- Auth erfolgt cookie-basiert (kein Bearer-Token erforderlich).
- Cloudflare/WAF kann aktiv sein (z. B. `cf_clearance`, `__cf_bm`).

## Aktuelle Erkenntnisse (Stand Mai 2026)
- Der ZIP-Endpunkt liefert in realen Tests stabil `200` mit `application/zip` und Dateiname `Deine REWE eBons.zip`.
- Der PDF-Endpunkt liefert in realen Tests stabil `200` mit `application/pdf` und Dateiname `Dein REWE eBon vom ...pdf`.
- Beide Endpunkte funktionieren ohne `Authorization`-Header, solange gültige Session-Cookies vorhanden sind.
- Die `customerId` ist eine UUID und kann serverseitig aus der aktiven Session über `GET /shop/mydata/couponwallet` als `customerUUID` aufgelöst werden.
- Der ZIP-Endpunkt funktioniert in realen Tests teils auch ohne expliziten Query-Parameter, solange die Session gültig ist.
- Session-Cookies können zwischen Requests rotieren (z. B. `rstp`), daher sind frisch ausgelesene Cookies wichtig.
- Cloudflare/WAF-Cookies (`cf_clearance`, `__cf_bm`) erhöhen die Erfolgsquote deutlich; ohne sie sind 403-Fälle wahrscheinlicher.

## V0-POC Ziel (kleinstes lauffähiges Inkrement)
- Input: `cookies-file` + `customerId`
- Aktion: ZIP-Endpunkt aufrufen und Datei speichern
- Erfolgskriterium: Entpackbare ZIP mit eBon-PDFs im lokalen Output-Verzeichnis
- Kein Muss für V0: Listen-Endpoint, Einzel-PDF-Fallback, SQLite-Import

## customerId-Auflösung im aktuellen Stand
- Priorität 1: explizit übergebene `--customer-id`
- Priorität 2: serverseitige Auflösung aus `GET /shop/mydata/couponwallet` (`customerUUID`) mit aktiver Session
- Priorität 3: Extraktion aus einer Eingabedatei, wenn dort ein kompletter Request oder eine URL mit `customerId=...` enthalten ist
- Priorität 4: Wiederverwendung eines lokal gecachten letzten erfolgreichen Werts (`tmp/rewe/customer_id.txt`)
- Falls keine Quelle greift, kann der ZIP-Abruf optional noch direkt über die Session versucht werden

### V0-Aufruf im Projekt
```bash
python fetch_tickets.py initial --retailer rewe --cookies-file rewe_cookies.json --customer-id <REWE_CUSTOMER_ID>
```

---

## Auth- und Session-Modell

## Prinzip
1. User meldet sich manuell im Browser bei REWE an.
2. Cookies werden lokal ausgelesen (Datei oder Browser-Profil).
3. HTTP-Session nutzt diese Cookies für API-Calls.
4. Bei Session-Expiry erfolgt Re-Auth über erneutes Cookie-Refresh.

## Unterstützte Cookie-Dateiformate im aktuellen POC
- JSON-Export (`[{"name": ..., "value": ...}]` oder `{ "cookies": [...] }`)
- Netscape-Cookie-Datei (tab-separiertes Browser-/Extension-Exportformat)
- roher `Cookie:`-Header aus den DevTools
- kompletter kopierter Request-Header, solange eine `Cookie:`-Zeile enthalten ist
- einfache `name=value`-Paare, getrennt durch `;` oder Zeilenumbrüche

## Relevante Cookie-Klassen
- Session-/Auth-Cookies (z. B. `rstp`, `_rdfa`)
- WAF/Cloudflare-Cookies (`cf_clearance`, `__cf_bm`, ggf. `_cfuvid`)
- Consent-Cookies sind meist nicht kritisch für den API-Zugriff, können aber Browser-nahe Requests stabilisieren.

## Hinweis
- Cookies sind oft kurzlebig oder werden rotiert.
- Deshalb: immer mit frischer Session starten und Laufzeit kurz halten.

---

## Empfohlener Abrufablauf

## Happy Path
1. Session initialisieren (`requests.Session` + Cookies laden)
2. `customerId` aus Session/Fallbacks auflösen
3. Optionalen Gesundheitscheck durchführen (ein leichter REWE-Endpoint)
4. ZIP-Download versuchen:
   - `GET /api/receipts/zip?customerId=...`
   - alternativ `GET /api/receipts/zip`, wenn die Session den Nutzerkontext bereits serverseitig auflöst
5. ZIP speichern und entpacken
6. Enthaltene PDFs an Parser/Pipeline übergeben
7. Metadaten persistieren (später SQLite)

## Fallback
- Wenn ZIP fehlschlägt (404/403/5xx):
  1. Receipt-IDs aus Listen-Endpoint holen
  2. Einzel-PDF pro ID über `/api/receipts/{id}/pdf` laden

---

## Fehlerbehandlung

## Erwartete Fehlerbilder
- `401 Unauthorized`: Session ungültig/abgelaufen
- `403 Forbidden`: WAF-Challenge oder fehlendes Browser-Signal
- `429 Too Many Requests`: Rate Limit
- `5xx`: temporäre Serverprobleme

## Strategie
- 401/403:
  - Session als ungültig markieren
  - Nutzer zum Cookie-Refresh auffordern
  - optional 1 automatischer Retry mit frisch geladener Session
- 429:
  - Exponential Backoff + Jitter
  - Request-Frequenz reduzieren
- 5xx/Timeout:
  - begrenzte Retries
  - danach sauber abbrechen mit verständlicher Fehlermeldung

---

## Sicherheit und Betrieb

## Sicherheitsregeln
- Cookie-Dateien niemals committen (`.gitignore`)
- Tokens/Cookies nicht im Log ausgeben
- Dateirechte für Cookie-Dateien restriktiv setzen
- Temporäre ZIP-Dateien nach Verarbeitung löschen

## Betriebsregeln
- Download-Chunks streamen (große ZIPs)
- Timeouts setzen
- Download-Verzeichnis klar trennen (`tmp/rewe/`)
- Idempotenz sicherstellen (Duplikate nicht mehrfach importieren)

---

## Architektur-Integration in `shopping-analyzer`

## Zielbild
- Neuer API-Client: `api/rewe_client.py`
- Neuer Workflow: `workflows/rewe_collector.py`
- Einheitliche Adapter-Schnittstelle (später): `ReceiptSource`

## Geplante Verantwortlichkeiten
- `rewe_client.py`
  - Session/Cookies anwenden
  - ZIP/PDF-Endpunkte aufrufen
  - robuste Fehlerbehandlung
- `rewe_collector.py`
  - Ablaufsteuerung (ZIP zuerst, PDF-Fallback)
  - Entpacken/Speichern
  - Übergabe an Parsing/Persistenz
- `storage/`
  - Ablage von Rohdateien und Importstatus

---

## Offene Punkte
1. Stabile Quelle für `customerId` definieren
2. Listen-Endpoint für Receipt-IDs final dokumentieren (Fallback)
3. Endgültiges Datenmodell für REWE-Import (direkt SQLite)
4. Entscheidung: Roh-PDFs dauerhaft speichern oder nur temporär

---

## Konkrete nächste Schritte
1. Minimalen `ReweClient` bauen (ZIP-Download + Healthcheck)
2. Session-Check + Retry/Backoff ergänzen
3. ZIP-Entpackung und PDF-Übergabe in einen REWE-Collector packen
4. Erst danach: Persistenz-Harmonisierung in SQLite

