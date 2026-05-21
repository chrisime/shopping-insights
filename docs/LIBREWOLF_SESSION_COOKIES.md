# LibreWolf: Session-Cookies für REWE aktivieren

## Problem

REWE setzt das Cookie `rstp` als **Session-Cookie** (ohne Ablaufdatum). Session-Cookies werden von Firefox/LibreWolf nur im Arbeitsspeicher gehalten – nicht in `cookies.sqlite`.

`browser_cookie3` liest nur `cookies.sqlite`, deshalb wird `rstp` nie gefunden.

Firefox schreibt Session-Cookies zusätzlich in die Session-Restore-Datei (`recovery.jsonlz4`), von wo unser Tool sie lesen kann. LibreWolf deaktiviert das aber standardmäßig über:

```
browser.sessionstore.privacy_level = 2
```

### Werte für `browser.sessionstore.privacy_level`

| Wert | Bedeutung |
|------|-----------|
| `0`  | Session-Cookies für alle Seiten im Session-Restore speichern |
| `1`  | Session-Cookies nur für unverschlüsselte (HTTP) Seiten speichern |
| `2`  | **Keine** Session-Cookies im Session-Restore speichern (**LibreWolf-Default**) |

## Lösung

### Option A: Über `about:config` (temporär)

1. LibreWolf öffnen
2. `about:config` in die Adressleiste eingeben
3. Nach `browser.sessionstore.privacy_level` suchen
4. Wert von `2` auf `0` ändern
5. LibreWolf neu starten
6. Bei REWE anmelden
7. Den Shopping-Analyzer erneut mit `--browser librewolf` starten

> **Hinweis:** LibreWolf kann diesen Wert bei Updates zurücksetzen, da er über `librewolf.cfg` als `defaultPref` gesetzt wird. Option B ist stabiler.

### Option B: Über `user.js` (dauerhaft)

Eine `user.js`-Datei im LibreWolf-Profil überschreibt alle Defaults persistent:

```bash
# Profil-Pfad (macOS)
PROFILE_DIR="$HOME/Library/Application Support/LibreWolf/Profiles"
PROFILE=$(ls -d "$PROFILE_DIR"/*default-default 2>/dev/null | head -1)

# user.js anlegen/erweitern
echo 'user_pref("browser.sessionstore.privacy_level", 0);' >> "$PROFILE/user.js"
```

Danach LibreWolf neu starten.

**Linux:**
```bash
PROFILE_DIR="$HOME/.librewolf"
PROFILE=$(ls -d "$PROFILE_DIR"/*default-default 2>/dev/null | head -1)
echo 'user_pref("browser.sessionstore.privacy_level", 0);' >> "$PROFILE/user.js"
```

### Option C: `--cookies-file` verwenden (kein Browser-Umbau nötig)

Falls du die LibreWolf-Einstellungen nicht ändern willst:

1. In LibreWolf bei REWE anmelden
2. Cookies exportieren (z.B. mit der Browser-Erweiterung „Cookie Editor" → Export → JSON)
3. Als `rewe_cookies.json` speichern
4. `--cookies-file rewe_cookies.json` verwenden

## Verifizierung

Nach der Änderung (Option A/B):

```bash
python3 fetch_tickets.py rewe --browser librewolf
```

Wenn `rstp` jetzt aus `recovery.jsonlz4` gelesen wird, erscheint:

```
  + 1 Session-Cookie(s) aus Librewolf-Session-Restore ergänzt
```

