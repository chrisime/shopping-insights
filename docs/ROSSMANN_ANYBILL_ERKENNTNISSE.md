# Rossmann-Filialbons über anybill

Stand 22. November 2026. Die Bedienung von Dashboard und CLI steht in der [Rossmann-Anleitung](../README_ROSSMANN_RECEIPTS.md).

## Konto-API

1. `POST /account.ws/v2/accounts/login` auf `rsmappapi.rossmann.net` erhält `email` und `password` als JSON. Der Standardlogin lässt die optionalen Felder für ein anonymes Konto weg. Die Antwort liefert `accountId` und `accountHash`.
2. `GET /account.ws/v2/accounts/{accountId}/receipt/auth` erhält den Header `Account-Hash` und liefert einen kurzlebigen anybill-`accessToken`.
3. Das Backend verwendet den Token als Bearer-Token für die Belegabfragen. Bei einem HTTP 401 stellt es einen neuen Token über `receipt/auth` aus und wiederholt den Belegrequest einmal.

Der Login antwortete im Vergleichstest ohne Plattformangaben mit einem leeren HTTP 400. App-Version, Build-Nummer und Korrelations-ID allein änderten das Ergebnis nicht. Nach Ergänzung von `Platform`, `Platform-Version` und `Build-Serial` lieferte Rossmann HTTP 200. Welches der drei Felder allein erforderlich ist, wurde nicht isoliert. Der Client sendet die im Live-Test bestätigte Kombination beim Login und bei der Token-Ausstellung, mit einer neuen Korrelations-ID pro Anfrage. Header und Versionswerte sind im [Auth-Modul](../auth/rossmann_auth.py) und in der [Rossmann-Konfiguration](../config/rossmann_config.py) hinterlegt.

Die früheren Versuche mit einem Webshop-Cookie-Export lieferten eine gültige Webshop-Sitzung, aber keine App-Kontoidentität. Der erprobte SSO-Aufruf endete mit HTTP 400 beziehungsweise einer Weiterleitung zur Loginseite. Die optionale Cookie-Datei kann eine bereits vorhandene App-Kontoidentität in den Feldern `accountId` und `accountHash` enthalten. Die Cookie-Diagnose prüft lokal Format und Cookies.

## Belegabruf und Speicherung

| anybill App API v4 auf `app.anybill.de` | Verwendung |
| --- | --- |
| `GET /api/v4/receipt` | Liste mit bis zu 100 Bons je Seite, nach Datum absteigend |
| `GET /api/v4/receipt/{id}` | Detail-JSON mit Artikelpositionen |
| `GET /api/v4/receipt/{id}/pdf` | Original-PDF für das lokale Archiv |

Der Client übernimmt den Antwort-Header `ContinuationToken` als Query-Parameter `continuationToken` der nächsten Seite. Sortierung und Seitengröße bleiben dabei gleich. Eine fehlgeschlagene Seite oder ein wiederholter Cursor beendet den Abruf mit einem Fehler. HTTP 429 und vorübergehende Serverfehler unterliegen begrenzten Wiederholungen mit exponentieller Wartezeit. [anybill-SDK-Dokumentation](https://developers.anybill.de/the_anybill_sdk/web_integration.html) · [Beleg-Client](../client/rossmann_client.py)

Der Online-Abruf gleicht die Beleg-IDs der Liste mit SQLite ab. Für neue IDs lädt er Detail-JSONs und versucht, das jeweilige Original-PDF herunterzuladen. Liegt ein Detail-JSON für eine noch nicht importierte ID bereits lokal vor, wird es wiederverwendet. Datum und Filiale stammen aus `head`, die Artikel aus `data.lines`. Der Parser übernimmt die Artikelzeilen samt Namen, Mengen und Preisen. PDF-Dateien dienen der Ablage. Der gemeinsame Importpfad validiert und speichert die Belege. [Rossmann-Workflow](../workflows/rossmann_workflow.py) · [Parser](../parsing/rossmann_receipt_parser.py)

### Coupons und Artikelpreise

Der Parser ordnet die Rabattbeträge aus den Artikelzeilen über `discountId` den Coupon-Bezeichnungen in `data.discounts` zu. Jede erkannte Coupon-Aktion wird mit ihrer Bezeichnung und der Summe ihrer Rabattbeträge gespeichert. Die Bezeichnung bestimmt die Zuordnung zu **10 % auf den gesamten Einkauf**, **Produktcoupons** oder **andere Coupons**.

Die Belegdetailansicht zeigt die gespeicherten Coupon-Zeilen unter **Deine Coupon-Ersparnis heute**. Für Artikel bevorzugt der Parser `pricePerUnitBeforeDiscounts`. Der Zahlbetrag des Bons stammt aus `data.fullAmountInclVat`. [Rossmann-Parser](../parsing/rossmann_receipt_parser.py) · [Dashboard-Anleitung](../README_ROSSMANN_RECEIPTS.md#coupons-im-dashboard)

## Dashboard-Import

Vue sendet die Anmeldedaten im Feld `rossmann_login` an `POST /imports/start`. Der Job authentifiziert sich über die Konto-API und verwendet danach die App-Kontoidentität für den gemeinsamen Rossmann-Workflow. Das Dashboard leert das Passwortfeld beim Absenden. Die Anwendung speichert das Passwort weder in SQLite noch in Jobstatus oder Fortschrittsereignissen. Über `GET /imports/{job_id}/events` kommen Fortschritt und Ergebnis zurück. [Import-API](../api/routes/imports.py) · [Hintergrundjob](../api/services/import_job_service.py) · [ADR-0007](../adr/0007-authenticate-rossmann-per-import.md)

## Verifikation

- Beim Live-Abruf wurden alle 20 von anybill gemeldeten Filialbons mit 89 Artikelpositionen in die reguläre SQLite-Datenbank übernommen. Der Rossmann-Händlerfilter zeigte anschließend 20 Bons.
- Beim erneuten Live-Abruf aus dem Dashboard lieferte anybill keine neuen Bons. Die bestehenden Beleg-IDs und Artikelpositionen blieben unverändert.
- Im Integrationstest liefert die simulierte Belegliste bei einem späteren Abruf einen zusätzlichen Bon. Der Job speichert ihn samt Artikel genau einmal. Ein weiterer Abruf meldet null neue Bons und null neue Artikel. [Integrationstest](../tests/test_api_imports.py)

## Quellen der Untersuchung

Die ursprüngliche Untersuchung verglich die Android-App 5.11.0, die anybill-Schnittstelle und Testanfragen mit Webshop-Cookies. Die dokumentierte App-Anfrage aus Version 5.11.1 diente als Referenz für den späteren Vergleichstest. [BonSync-Untersuchung](https://github.com/kurim/BonSync-Store/blob/main/rossmann/api-rossmann.md)
