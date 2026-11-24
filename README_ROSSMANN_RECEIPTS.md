# Rossmann-Filialbons abrufen

Die Integration liest digitale **Filialbons** aus dem Rossmann-Konto und speichert sie samt Artikelpositionen in der gemeinsamen Datenbank `shopping_receipts.sqlite`. Online-Bestellungen liegen außerhalb dieses Imports.

Du findest die verfügbaren Filialbons in der Rossmann-App unter **Mehr → Meine Einkäufe → Filiale**. Rossmann ordnet einen digitalen Bon deinem Konto zu, wenn du die digitale Kundenkarte beim Einkauf an der Kasse scannen lässt. [Rossmann-App-Hilfe](https://www.rossmann.de/de/service-und-hilfe/faq/de_de/category/app)

## Im Dashboard abrufen

1. Starte das Backend und das Vue-Dashboard wie in der [Projektanleitung](./readme.md#dashboard) beschrieben.
2. Öffne **Import** und wähle unter **Importieren für** den Händler **Rossmann**.
3. Wähle **Rossmann-Konto**, gib E-Mail und Passwort ein und klicke auf **Import**. Die Anwendung verwendet die Zugangsdaten für diesen Abruf und leert das Passwortfeld beim Absenden.
4. Wechsle nach **Rossmann-Import abgeschlossen** zu **Ausgaben** oder **Artikel** und setze den Händlerfilter auf **Rossmann**. Prüfe den Datumsbereich, falls du ihn zuvor eingeschränkt hast.

Für spätere Filialbons startest du denselben Abruf erneut. Der Import gleicht die Beleg-IDs mit SQLite ab und verarbeitet neue Bons samt Artikeln. Sind alle gelieferten Bons bereits gespeichert, bleibt der Zähler **Neu** bei 0.

## Coupons im Dashboard

Unter **Ausgaben → Kennzahlen** siehst du die Coupon-Ersparnis für den ausgewählten Zeitraum.

| Karte | Anzeige |
| --- | --- |
| **Rossmann 10% Coupon** | Ersparnis aus den 10-%-Coupons auf den gesamten Einkauf |
| **Rossmann Produktcoupons** | Ersparnis aus Produktcoupons und Sparquote bezogen auf den bezahlten Rossmann-Betrag |
| **Rossmann andere Coupons** | Ersparnis aus Coupons, deren Bezeichnung keinen der beiden Typen erkennen lässt. Die Karte erscheint bei einer positiven Summe. |

Die Zuordnung beruht auf der Coupon-Bezeichnung auf dem Bon. Rossmann-Rabatte fließen in die gemeinsame Kennzahl **Gesamter Preisvorteil** ein.

### Einzelne Coupons im Filialbon

Setze den Händlerfilter auf **Rossmann** und klicke unter **Ausgaben** auf einen Balken im Diagramm **Ausgaben über Zeit** oder unter **Artikel** auf einen Eintrag in **Top-Artikel**. Sind mehrere Bons verfügbar, blättere mit **Zurück** und **Weiter**.

Im Belegdetail listet **Deine Coupon-Ersparnis heute** die erkannten Coupons mit ihrer Bezeichnung und Ersparnis in Euro auf. Die Artikelpositionen zeigen die Stückpreise vor Rabatt. Die Summe am Ende des Bons ist der bezahlte Betrag.

## Per CLI abrufen, lokal importieren und exportieren

Führe die Befehle im Projektverzeichnis aus.

```bash
# Neue Filialbons online abrufen und importieren (auch für spätere Abrufe)
uv run --locked python fetch_tickets.py initial --retailer rossmann --login

# Bereits heruntergeladene Detail-JSONs lokal erneut importieren
uv run --locked python fetch_tickets.py update --retailer rossmann --output-dir tmp/rossmann

# Gespeicherte Rossmann-Bons als JSON exportieren
uv run --locked python fetch_tickets.py export --retailer rossmann --output-file rossmann_receipts.json
```

`--login` fragt E-Mail und Passwort im Terminal ab. Eine Cookie-Datei ist für diesen Weg entbehrlich. `update` verwendet die lokalen Dateien und stellt keine Verbindung zu Rossmann her.

Bei älteren Importen ergänzt `update` die Rabattbeträge, Coupon-Kategorien und einzelnen Coupon-Zeilen aus den vorhandenen Detail-JSONs.

## Dateien

| Pfad | Inhalt |
| --- | --- |
| `shopping_receipts.sqlite` | Normalisierte Bons und Artikel aller Händler |
| `tmp/rossmann/receipts/` | Detail-JSONs der abgerufenen Filialbons |
| `tmp/rossmann/pdf/` | Heruntergeladene Originalbons als PDF |
| `tmp/rossmann/rossmann_skipped_receipts.json` | Gründe für übersprungene Bons, falls beim lokalen Import welche anfallen |
| `rossmann_receipts.json` | Optionaler JSON-Export aus SQLite |

## Fehler beim Abruf

- Bei **Rossmann-Anmeldung fehlgeschlagen** prüfe die Anmeldung mit demselben Konto in der Rossmann-App. Bei wiederholtem HTTP 400 trotz funktionierender App-Anmeldung hilft der Abschnitt zur [Konto-API](./docs/ROSSMANN_ANYBILL_ERKENNTNISSE.md#konto-api) bei der technischen Diagnose.
- Der alternative Modus **Cookie-Datei** setzt eine Datei mit der App-Kontoidentität (`accountId` und `accountHash`) voraus. Ein Webshop-Cookie-Export allein reicht für den Abruf nicht aus. `uv run --locked python fetch_tickets.py check --retailer rossmann --cookies-file rossmann_cookies.json` prüft die Cookie-Datei lokal. Die Prüfung sagt nichts darüber aus, ob ein anybill-Token ausgestellt werden kann.
- Bei einer Meldung über fehlgeschlagene Belegdetails starte den Online-Abruf erneut. Bereits lokal gespeicherte Detail-JSONs können beim Wiederholen verwendet werden.
