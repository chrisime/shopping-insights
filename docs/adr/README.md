# ADR-Übersicht

Stand: 2026-05-10

Dieses Verzeichnis enthält die dokumentierten Architekturentscheidungen des Projekts.

## Lesereihenfolge

1. [`0002-shared-receipt-normalization-layer.md`](./0002-shared-receipt-normalization-layer.md)
2. [`0003-package-layer-rules-and-wrapper-removal.md`](./0003-package-layer-rules-and-wrapper-removal.md)
3. [`0001-rewe-login-mfa-cookie-extraction.md`](./0001-rewe-login-mfa-cookie-extraction.md) bei Bedarf für den historischen REWE-Login-Kontext

## Inhalt

- [`0001-rewe-login-mfa-cookie-extraction.md`](./0001-rewe-login-mfa-cookie-extraction.md)
  - beschreibt den historischen Umgang mit REWE-Login, MFA und Cookie-Gewinnung
- [`0002-shared-receipt-normalization-layer.md`](./0002-shared-receipt-normalization-layer.md)
  - führt die gemeinsame Receipt-Normalisierung über `shared.receipt_schema` und `shared.addresses` ein
- [`0003-package-layer-rules-and-wrapper-removal.md`](./0003-package-layer-rules-and-wrapper-removal.md)
  - dokumentiert die Zielarchitektur ohne Wrapper, die kanonischen Importpfade und die Entkopplung des Pipeline-Runners

## Aktuell maßgeblich für neue Beiträge

Für neue Architekturänderungen sind vor allem ADR 0002 und ADR 0003 relevant:

- ADR 0002 definiert die gemeinsamen Schema-Bausteine
- ADR 0003 definiert die Paketgrenzen, Importpfade und Orchestrierungsregeln

Zusammen mit [`../architecture/package-layer-rules.md`](../architecture/package-layer-rules.md) und [`../architecture/workflow-overview.md`](../architecture/workflow-overview.md) bilden sie die aktuelle Zielarchitektur.

