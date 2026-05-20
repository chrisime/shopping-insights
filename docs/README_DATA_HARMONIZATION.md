# Datenharmonisierung LIDL vs. REWE

Diese Notiz beschreibt den aktuellen Stand der Harmonisierung zwischen LIDL- und REWE-Bons.

## Ziel

Ziel der Harmonisierung ist ein gemeinsames Auswertungsmodell, sodass beide Haendler in derselben Datenbank konsistent verglichen werden koennen.

Aktueller Persistenzpfad:

- `shopping_receipts.sqlite` (DB-first)

## Was bereits harmonisiert ist

- gemeinsames Basis-Schema fuer Belege (`id`, `retailer`, `purchase_date`, `items`, `payment_methods`, `total_price`)
- zentrale Normalisierung von Datumswerten (`purchase_date` als ISO `yyyy-mm-dd`)
- gemeinsame Persistenzlogik ueber den Store-Port
- gemeinsame Dashboard-/Export-Basis aus demselben DB-Stand

## Was noch nicht vollstaendig harmonisiert ist

- haendlerspezifische Bonus-/Rabattfelder bleiben getrennt:
  - LIDL: `lidlplus_amount_saved`, `sticker_discount_amount`
  - REWE: `rewe_bonus_amount`, `rewe_bonus_total_amount`, `rewe_bonus_amount_saved`
- unterschiedliche Rohquellen und Extraktionspfade:
  - LIDL: API/HTML-Tickets
  - REWE: ZIP/PDF-Parsing
- unterschiedliche Delta-Mechanik:
  - LIDL: API-Seiten-Scan plus stabile `receipt_id`
  - REWE: kein serverseitiger Delta-Endpunkt, `update` basiert auf lokal vorhandenen PDFs

## Praktische Folge fuer Auswertungen

- Basisvergleiche (z. B. Gesamtsumme, Artikelanzahl, Einkaufsdatum) sind bereits gut vergleichbar.
- Bonus-/Rabattvergleiche muessen aktuell haendlerspezifisch interpretiert werden.
- Bei tiefer Feldsemantik (z. B. Payment-Details, Artikelklassifikation) kann es weiterhin source-bedingte Unterschiede geben.

## Geplanter Ausbau

Moegliche naechste Schritte zur weitergehenden Harmonisierung:

1. ein gemeinsames, abstrahiertes Bonusmodell ueber beide Haendler
2. strengere Feld-Mapping-Regeln pro Parser mit zentralen Konvertierungsprofilen
3. ein dokumentierter Harmonisierungsgrad pro Feld (voll/teilweise/haendlerspezifisch)

