import json
import shutil
from pathlib import Path

from parsing.receipt_schema import normalize_receipt_schema
from storage import save_receipts_to_json

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "tmp" / "schema_migration_backups_20260508"
FILES = [
    (ROOT / "lidl_receipts.json", "lidl"),
    (ROOT / "rewe_receipts.json", "rewe"),
]

BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def collect_keys(receipts):
    keys = set()
    for receipt in receipts:
        keys.update(receipt.keys())
    return keys


for path, retailer in FILES:
    with open(path, "r", encoding="utf-8") as file:
        raw_receipts = json.load(file)

    backup_path = BACKUP_DIR / path.name
    shutil.copy2(path, backup_path)

    normalized_receipts = [
        normalize_receipt_schema(receipt, retailer=retailer) for receipt in raw_receipts
    ]

    before_keys = collect_keys(raw_receipts)
    after_keys = collect_keys(normalized_receipts)
    removed_keys = sorted(before_keys - after_keys)
    added_keys = sorted(after_keys - before_keys)

    changed_examples = []
    for raw, normalized in zip(raw_receipts[:5], normalized_receipts[:5]):
        changed_fields = {}
        for key in after_keys:
            raw_value = raw.get(key, "<missing>")
            normalized_value = normalized.get(key, "<missing>")
            if raw_value != normalized_value:
                changed_fields[key] = {
                    "before": raw_value,
                    "after": normalized_value,
                }
        if changed_fields:
            changed_examples.append(
                {
                    "id": normalized.get("id") or normalized.get("url"),
                    "changed_fields": changed_fields,
                }
            )

    save_receipts_to_json(normalized_receipts, file_path=str(path), retailer=retailer)

    print(f"FILE: {path.name}")
    print(f"  retailer: {retailer}")
    print(f"  receipts: {len(raw_receipts)}")
    print(f"  backup: {backup_path}")
    print(f"  added_keys: {added_keys}")
    print(f"  removed_keys: {removed_keys}")
    print(f"  changed_examples: {json.dumps(changed_examples, ensure_ascii=False)[:1800]}")
    print()

