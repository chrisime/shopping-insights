# ADR 0001: REWE Login mit interaktiver MFA und automatischer Cookie-Extraktion

- **Status:** Angenommen
- **Datum:** 2026-05-07
- **Entscheider:** Projektmaintainer
- **Bezug:** `README_REWE_EBONS.md`, `REWE_EBON_ABRUF_SKIZZE.md`, `auth/rewe_file_auth.py`, `auth/rewe_customer_id.py`, `api/rewe_client.py`

## Kontext

Der aktuelle REWE-POC funktioniert technisch zuverlässig, solange eine gültige REWE-Session als Cookies vorliegt.

Der aktuelle Ablauf ist jedoch unkomfortabel:

1. Der Benutzer meldet sich manuell im Browser bei REWE an.
2. Der Benutzer exportiert Cookies manuell oder kopiert Request-/Header-Daten.
3. Der POC liest diese Cookies aus einer Datei ein.
4. Die `customerId` wird bevorzugt aus `GET /shop/mydata/couponwallet` als `customerUUID` ermittelt.
5. Anschließend erfolgt der Download über die REWE-Receipt-Endpunkte.

Dabei gelten folgende Randbedingungen:

- REWE verwendet kurzlebige Session-Cookies.
- Cloudflare-/WAF-Cookies sind oft relevant für erfolgreiche Requests.
- Im Benutzerkonto ist MFA aktiviert.
- Ein rein technischer Login mit Benutzername/Passwort reicht deshalb nicht aus.
- Eine automatische Umgehung von MFA ist nicht Ziel des Projekts.
- Der größte aktuelle Schmerzpunkt ist die **manuelle Cookie-Extraktion**.

Ziel ist daher ein Login-Prozess, der den Komfort erhöht, ohne MFA zu umgehen oder unnötig sensible Geheimnisse zu speichern.

## Entscheidung

Wir führen für REWE einen **browsergestützten, interaktiven Login-Prozess** ein.

### Kernaussage

Die Anwendung automatisiert **nicht** den vollständigen REWE-Login inklusive MFA im Hintergrund.

Stattdessen wird eine **bereits vom Benutzer bestätigte Browser-Session** automatisch übernommen.

Praktisch bedeutet das im aktuellen Stand:

- der dateibasierte Cookie-/Request-Import ist der verlässlichste empfohlene Standardpfad
- Browserprofil-Reuse ist ein Best-Effort-Pfad
- der interaktive Selenium-Login ist nur ein ergänzender experimenteller Pfad und kein verlässlicher Weg unter aktiver Mensch-/WAF-Prüfung

### Gewählter Zielprozess

1. Die Anwendung startet einen **sichtbaren Browser-Kontext** oder nutzt ein vorhandenes lokales Browser-Profil.
2. Optional kann der Benutzer **Benutzername und Passwort** an die Anwendung übergeben.
3. Die Anwendung darf diese Zugangsdaten nur verwenden, um den **ersten Login-Schritt** zu erleichtern.
4. **MFA bleibt immer interaktiv und benutzergesteuert**.
5. Nach erfolgreicher Anmeldung und MFA-Bestätigung extrahiert die Anwendung die REWE-Cookies automatisch.
6. Die extrahierten Cookies werden direkt in eine `requests.Session` oder einen äquivalenten Session-Container übernommen.
7. Anschließend läuft der bestehende REWE-Abruf unverändert weiter:
   - `customerUUID` aus `couponwallet`
   - ZIP-Download
   - PDF-Extraktion
8. Als Fallback bleibt der bestehende **Datei-basierte Cookie-Import** erhalten.

## Architekturentscheidung

Es wird eine klare Trennung zwischen **Login/Session-Erzeugung** und **fachlichem Abruf** eingeführt.

### Zielbausteine

#### 1. `ReweSessionProvider`
Verantwortlich für das Bereitstellen einer authentifizierten REWE-Session.

Geplante Implementierungen:

- `ReweBrowserProfileSessionProvider`
  - liest Cookies direkt aus einem lokalen Browser-Profil
  - analog zum bestehenden Lidl-Ansatz in `auth/browser_auth.py`
  - bevorzugter schneller Pfad, wenn der Benutzer bereits im Browser angemeldet ist

- `ReweInteractiveLoginSessionProvider`
  - startet einen sichtbaren Browser mit persistentem Kontext
  - unterstützt optional Benutzername/Passwort für den ersten Login-Schritt
  - wartet anschließend auf manuelle MFA-Bestätigung
  - übernimmt danach Cookies automatisiert aus dem Browser-Kontext

- `ReweFileSessionProvider`
  - nutzt bestehende Datei-Import-Mechanik aus `auth/rewe_file_auth.py`
  - bleibt Fallback und Debug-/Recovery-Pfad

#### 2. `ReweCustomerIdResolver`
Bleibt getrennt und liest die `customerUUID` aus:

- primär `GET /shop/mydata/couponwallet`
- sekundär Datei-/Cache-Fallbacks

#### 3. `ReweClient`
Bleibt fachlich zuständig für:

- Session-Test
- ZIP-Download
- Entpacken
- Fehlerbehandlung

Der `ReweClient` soll **nicht** für Login, Passwortverwaltung oder MFA-Orchestrierung verantwortlich sein.

## Entscheidung im Detail

### Bevorzugter Modus

**Bevorzugt wird Session-Reuse über einen echten Browser-Kontext.**

Begründung:

- MFA ist bereits Teil des regulären Benutzerflusses.
- Ein echter Browser ist näher am REWE-/Cloudflare-Verhalten als rohe HTTP-Logik.
- Nach erfolgreicher MFA kann die Sitzung lokal weiterverwendet werden.
- Der technische Risiko- und Wartungsaufwand ist deutlich geringer als bei vollautomatischem Login.

### Umgang mit Benutzername/Passwort

Benutzername und Passwort dürfen **optional** unterstützt werden, aber nur unter diesen Bedingungen:

- nur für den initialen Login-Schritt
- kein Versuch, MFA zu automatisieren oder zu umgehen
- keine dauerhafte Speicherung im Klartext
- bevorzugt nur im laufenden Prozessspeicher
- falls Persistenz nötig wird: ausschließlich über Betriebssystem-Mechanismen wie Keychain/Credential Store

### Umgang mit MFA

MFA ist **explizit im Scope als interaktiver Schritt**, aber **nicht** als vollautomatischer Schritt.

Das bedeutet:

- Die Anwendung darf den Benutzer anweisen, MFA im sichtbaren Browser-Fenster abzuschließen.
- Die Anwendung darf auf ein Erfolgssignal warten, z. B. Weiterleitung auf eine bekannte Seite oder das Vorliegen bestimmter Session-Cookies.
- Die Anwendung speichert keine OTP-Secrets, TOTP-Seeds oder Recovery-Codes.
- Es wird keine Logik implementiert, die MFA technisch aushebelt.

## Erwogene Optionen

### Option A: Weiter wie bisher mit manuellem Cookie-Export

**Beschreibung**
- Benutzer exportiert Cookies manuell.
- POC bleibt dateibasiert.

**Vorteile**
- minimaler Implementierungsaufwand
- technisch bereits funktionsfähig

**Nachteile**
- schlechte Benutzererfahrung
- fehleranfällig
- wiederholter manueller Aufwand
- unnötige Reibung beim regelmäßigen Abruf

**Entscheidung**
- Nicht bevorzugt, aber als Fallback beibehalten.

### Option B: Vollautomatischer Login mit Benutzername/Passwort und MFA-Automatisierung

**Beschreibung**
- Anwendung loggt sich selbstständig ein und automatisiert auch MFA.

**Vorteile**
- maximaler Komfort auf dem Papier

**Nachteile**
- hohe technische Fragilität
- deutlich höheres Sicherheitsrisiko
- problematische Geheimnisverwaltung
- potenziell konfliktträchtig hinsichtlich Schutzmechanismen und Nutzungsbedingungen
- unnötig komplex für den eigentlichen Nutzen

**Entscheidung**
- Verworfen.

### Option C: Browsergestützter Login mit manueller MFA und automatischer Cookie-Extraktion

**Beschreibung**
- Sichtbarer Browser
- optional Credential-Prefill
- MFA durch Benutzer
- automatische Cookie-Übernahme danach

**Vorteile**
- gute Balance aus Komfort, Robustheit und Sicherheit
- kompatibel mit MFA
- näher am realen Nutzerverhalten
- reduziert manuelle Schritte deutlich

**Nachteile**
- weiterhin ein interaktiver Schritt nötig
- Browser-/OS-Abhängigkeiten
- Keychain-/Profilzugriff kann je nach Plattform haken

**Entscheidung**
- Angenommen.

## Konsequenzen

### Positive Konsequenzen

- Der Benutzer muss Cookies nicht mehr manuell exportieren.
- MFA bleibt mit der Sicherheitsrealität des Kontos kompatibel.
- Die bestehende fachliche Abruflogik kann weitgehend unverändert bleiben.
- Der Login-Prozess wird benutzerfreundlicher und wartbarer.

### Negative Konsequenzen

- Es gibt weiterhin keinen vollständig headless Hintergrund-Login.
- Ein sichtbarer Browser oder ein zugängliches Browser-Profil wird benötigt.
- Manche Plattform-/Browser-Kombinationen können Probleme beim Cookie-Zugriff verursachen.
- Sessions bleiben kurzlebig; erneute Anmeldung kann nötig sein.

## Sicherheits- und Betriebsregeln

1. Zugangsdaten werden nicht im Klartext auf Platte gespeichert.
2. MFA-Secrets werden nie gespeichert.
3. Cookies gelten als sensible Authentifizierungsdaten.
4. Persistierte Cookies sind nur lokal und möglichst kurzlebig zu halten.
5. Logs dürfen keine Cookies, Tokens, Passwörter oder MFA-Codes enthalten.
6. Der manuelle Datei-Fallback bleibt verfügbar, wenn Browser-Extraktion fehlschlägt.

## Empfohlene technische Ausgestaltung

### Phase 1: Browser-Profil-Extraktion

Zuerst wird ein REWE-spezifischer Browser-Extraktor eingeführt, analog zu `auth/browser_auth.py`:

- Unterstützung für `firefox`, `chrome`, `chromium`
- Filterung auf `rewe.de`
- direkte Übernahme in eine `requests.Session`
- Wiederverwendung für `couponwallet` und ZIP-Download

Ziel: Benutzer loggt sich wie bisher selbst im Browser ein, die Anwendung liest danach die Cookies automatisch aus dem Browserprofil.

### Phase 2: Interaktiver Login-Flow

Anschließend optional:

- sichtbarer Browser via Automation mit persistentem Kontext
- Login-Seite öffnen
- auf manuelle MFA warten
- Cookies aus dem Browser-Kontext übernehmen

Ziel: Der Benutzer muss nicht mehr selbst den Browser öffnen und später separat Cookies exportieren.

Stand Mai 2026:

- eine erste Phase-2-Variante ist implementiert
- der Browser wird sichtbar gestartet
- ein Benutzername kann optional fuer den Login vorausgefuellt werden
- das Passwort wird nur verdeckt zur Laufzeit abgefragt und nicht persistiert
- Login und MFA bleiben manuell
- anschließend werden die Live-Cookies in eine `requests.Session` übernommen
- unter aktiver Mensch-/WAF-Pruefung ist dieser Pfad jedoch nicht als verlässlicher Standard zu betrachten

### Aktueller empfohlener Betriebsmodus

Fuer den regulaeren Einsatz wird aktuell empfohlen:

1. regulaeren Browser verwenden
2. Cookies bzw. einen kopierten Request exportieren
3. Datei mit dem REWE-Diagnosepfad pruefen
4. dateibasierten REWE-Abruf starten

### Phase 3: Komfort und Stabilisierung

Optional später:

- Session-Frische prüfen
- Re-Auth-Hinweise verbessern
- lokale sichere Credential-Speicherung über OS-Keychain evaluieren
- Browser-spezifische Fehlerbilder sauber abfangen

## Nicht im Scope

Folgende Dinge sind ausdrücklich nicht Teil dieser Entscheidung:

- MFA-Bypass oder MFA-Automatisierung
- Speichern von OTP-Secrets oder TOTP-Seeds
- rein headless Login ohne Benutzerinteraktion
- Umgehung von WAF-/Schutzmechanismen
- dauerhafte zentrale Speicherung von REWE-Zugangsdaten

## Akzeptanzkriterien

Die Entscheidung gilt als erfolgreich umgesetzt, wenn:

1. Ein Benutzer nach normalem Login inklusive MFA **ohne manuellen Cookie-Export** einen REWE-Abruf starten kann.
2. Die Anwendung Cookies automatisiert in eine Session übernehmen kann.
3. `customerUUID` weiterhin aus `couponwallet` ermittelt wird.
4. Der bestehende Datei-Fallback weiterhin funktioniert.
5. Es keine Speicherung von MFA-Geheimnissen gibt.

## Offene Punkte

1. Soll zuerst nur Browser-Profil-Extraktion kommen oder direkt auch ein interaktiver Browser-Login?
2. Welcher Browser wird für den ersten stabilen Rollout bevorzugt: Firefox oder Chromium?
3. Sollen Benutzername/Passwort überhaupt in der CLI erlaubt sein oder nur in einem interaktiven Prompt?
4. Soll eine optionale OS-Keychain-Integration für Zugangsdaten vorgesehen werden?

## Kurzfassung

Die empfohlene Richtung ist **nicht** „vollautomatischer Login trotz MFA“, sondern:

**interaktiver Browser-Login + manuelle MFA + automatische Cookie-Extraktion + bestehender Session-basierter REWE-Abruf**.

Das ist die beste Balance aus:

- Benutzerkomfort
- technischer Stabilität
- MFA-Kompatibilität
- Sicherheitsniveau
- geringer Komplexität

