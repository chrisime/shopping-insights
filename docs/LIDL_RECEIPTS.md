# LIDL-Kassenbons extrahieren

Diese Anleitung beschreibt den aktuellen LIDL-Workflow des Projekts: Session aufbauen, API testen, Bons abrufen, parsen, validieren und in `lidl_receipts.json` speichern.

---

## Was der aktuelle Stand kann

Der LIDL-Workflow kann aktuell:

- Cookies direkt aus unterstützten Browserprofilen übernehmen
- exportierte Cookie-Dateien einlesen
- die LIDL-Session vor dem eigentlichen Abruf testen
- alle historischen verfügbaren Bons importieren (`initial`)
- nur neue Bons seit dem letzten Lauf ergänzen (`update`)
- Cookie-Dateien vorab per Diagnose prüfen (`check`)
- die importierten Daten in `lidl_receipts.json` persistieren

---

## Wichtige Einschränkung

LIDL stellt Kassenbondaten nach aktuellem Stand nur ab **Februar 2023** bereit. Ältere Bons sind über den verfügbaren Abrufpfad in der Regel nicht mehr erreichbar.

---

## Voraussetzungen

Du brauchst:

- Python 3.10 oder neuer
- installierte Projekt-Abhängigkeiten aus `requirements.txt`
- ein eingeloggtes LIDL-Konto
- entweder ein lokales Browserprofil oder eine exportierte Cookie-Datei

Installation:

```bash
git clone <repository-url>
cd shopping-analyzer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Unter Windows:

```cmd
venv\Scripts\activate
```

---

## Authentifizierung

### Empfohlen: Browserprofil

Unterstützte Browser:

- `firefox`
- `librewolf`
- `chrome`
- `chromium`

Beispiel:

```bash
python get_data.py initial --retailer lidl --browser firefox
```

Hinweis für macOS: Wenn Chrome beim Cookie-Zugriff Probleme mit dem Schlüsselbund macht, ist Firefox oft der robustere Pfad.

### Alternative: Cookie-Datei

Du kannst Cookies auch manuell exportieren, zum Beispiel mit einer Browser-Erweiterung wie EditThisCookie, und in einer Datei wie `lidl_cookies.json` speichern.

Beispiel:

```bash
python get_data.py initial --retailer lidl --cookies-file lidl_cookies.json
```

---

## Cookie-Datei prüfen

Bevor du den eigentlichen Import startest, kannst du eine exportierte Cookie-Datei prüfen:

```bash
python get_data.py check --retailer lidl --cookies-file lidl_cookies.json
```

Die Diagnose prüft unter anderem:

- ob die Datei lesbar ist
- ob LIDL-Cookies erkannt werden
- ob wichtige Cookies wie `authToken` vorhanden sind
- ob die Datei eher direkt nutzbar oder wahrscheinlich unvollständig ist

---

## Historischen Import starten

Für den ersten vollständigen Import:

```bash
python get_data.py initial --retailer lidl --cookies-file lidl_cookies.json
```

Optional mit Browserprofil:

```bash
python get_data.py initial --retailer lidl --browser firefox
```

Optional mit Länder-Override:

```bash
python get_data.py initial --retailer lidl --cookies-file lidl_cookies.json --country de
```

---

## Spätere Updates

Um nur neue Bons hinzuzufügen:

```bash
python get_data.py update --retailer lidl --cookies-file lidl_cookies.json
```

Optional mit Browserprofil:

```bash
python get_data.py update --retailer lidl --browser firefox
```

Der Update-Lauf prüft nur die konfigurierten jüngsten Seiten und ergänzt fehlende Bons in der bestehenden Datei.

---

## Interaktives Menü

Alternativ kannst du den Workflow interaktiv starten:

```bash
python get_data.py
```

Im LIDL-Menü stehen aktuell zur Verfügung:

1. Initial Setup
2. Update
3. Cookie-Datei prüfen (Diagnose)
4. Zurück

---

## Ausgabe

Der LIDL-Workflow schreibt die importierten Bons nach:

- `lidl_receipts.json`

Zusätzlich kann bei übersprungenen Bons ein Report mit Skip-Gründen geschrieben werden.

---

## Dashboard

Nach dem Import kannst du das Dashboard starten:

```bash
streamlit run dashboard.py
```

---

## Sicherheitshinweise

Cookie-Dateien enthalten sensible Login-Daten.

Bitte beachte:

- niemals committen
- niemals weitergeben
- lokal sicher speichern
- nach Möglichkeit nach erfolgreichem Import löschen

