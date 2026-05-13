"""SQLite-backed receipt store with relational projections and payload hashes."""

from __future__ import annotations

import hashlib
import simplejson
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from config import get_receipt_schema_profile
from result_types import PersistResult
from shared.receipt_schema import normalize_receipt_schema
from shared.receipt_store import ReceiptStore

from .sqlite_domains import (
    PaymentMethodDomain,
    PurchaseDomain,
    PurchaseItemDomain,
    PurchaseLidlDomain,
    PurchaseReweDomain,
    RetailerDomain,
    StoreDomain,
)
from .sqlite_entity_builders import (
    build_payment_method_entities,
    build_purchase_entity,
    build_purchase_item_entities,
    build_purchase_lidl_entity,
    build_purchase_rewe_entity,
    build_retailer_entity,
    build_store_entity,
)
from .sqlite_migration_runner import apply_sqlite_migrations

DEFAULT_SQLITE_RECEIPTS_FILE = "shopping_receipts.sqlite"


def _resolve_receipts_db_path(file_path: Optional[str] = None) -> str:
    """Resolve the SQLite database file path used for receipt persistence."""
    return file_path or DEFAULT_SQLITE_RECEIPTS_FILE


def _connect_sqlite(file_path: str) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys enabled and schema ensured."""
    db_path = Path(file_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("pragma foreign_keys = on")
    _ensure_schema(connection)
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    """Apply all pending SQLite migrations before the store is used."""
    apply_sqlite_migrations(connection)
    connection.commit()


def _calculate_receipt_payload_hash(receipt_data: Dict[str, Any]) -> str:
    """Render a normalized receipt dict into a canonical hash for change detection."""
    value = simplejson.dumps(
        receipt_data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    text = "" if value is None else value
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _persist_receipt_row(
    receipt_data: Dict[str, Any],
    payload_hash: str,
    *,
    store_domain: StoreDomain,
    purchase_domain: PurchaseDomain,
    purchase_item_domain: PurchaseItemDomain,
    payment_method_domain: PaymentMethodDomain,
    purchase_lidl_domain: PurchaseLidlDomain,
    purchase_rewe_domain: PurchaseReweDomain,
) -> Optional[str]:
    """Persist one receipt and return whether it was created, updated or unchanged."""
    retailer_code = str(receipt_data.get("retailer") or "").strip().lower()
    store_entity = build_store_entity(receipt_data)

    store_id = store_domain.resolve_id(store_entity)
    purchase_entity = build_purchase_entity(receipt_data, store_id, payload_hash)
    action = purchase_domain.persist(purchase_entity)
    if action is None:
        return None

    if retailer_code == "lidl":
        purchase_lidl_domain.insert(build_purchase_lidl_entity(receipt_data))
    elif retailer_code == "rewe":
        purchase_rewe_domain.insert(build_purchase_rewe_entity(receipt_data))

    purchase_item_domain.insert_many(build_purchase_item_entities(receipt_data))
    payment_method_domain.insert_many(build_payment_method_entities(receipt_data))
    return action


class SqliteReceiptStore(ReceiptStore):
    """SQLite-backed receipt store used for relational persistence plus delta checks."""

    def find_existing_ids(
        self,
        retailer: str,
        file_path: Optional[str] = None,
    ) -> set[str]:
        db_path = _resolve_receipts_db_path(file_path)
        with closing(_connect_sqlite(db_path)) as connection:
            purchase_domain = PurchaseDomain(connection)
            return purchase_domain.find_ids_by_retailer(retailer.lower())

    def persist_receipts(
        self,
        receipts: Sequence[Dict[str, Any]],
        retailer: str,
        file_path: Optional[str] = None,
    ) -> PersistResult:
        db_path = _resolve_receipts_db_path(file_path)
        retailer_code = retailer.lower()
        created_count = 0
        updated_count = 0
        receipt_schema_profile = get_receipt_schema_profile(retailer_code)
        retailer_entity = build_retailer_entity(retailer_code)

        with closing(_connect_sqlite(db_path)) as connection:
            retailer_domain = RetailerDomain(connection)
            store_domain = StoreDomain(connection)
            purchase_domain = PurchaseDomain(connection)
            purchase_item_domain = PurchaseItemDomain(connection)
            payment_method_domain = PaymentMethodDomain(connection)
            purchase_lidl_domain = PurchaseLidlDomain(connection)
            purchase_rewe_domain = PurchaseReweDomain(connection)

            with connection:
                retailer_domain.upsert(retailer_entity)

                for receipt in receipts:
                    normalized_receipt = normalize_receipt_schema(
                        receipt,
                        retailer=retailer_code,
                        profile=receipt_schema_profile,
                    )
                    receipt_id = normalized_receipt.get("id") or normalized_receipt.get("url")
                    if not receipt_id:
                        continue
                    normalized_receipt["id"] = str(receipt_id)
                    payload_hash = _calculate_receipt_payload_hash(normalized_receipt)
                    action = _persist_receipt_row(
                        normalized_receipt,
                        payload_hash,
                        store_domain=store_domain,
                        purchase_domain=purchase_domain,
                        purchase_item_domain=purchase_item_domain,
                        payment_method_domain=payment_method_domain,
                        purchase_lidl_domain=purchase_lidl_domain,
                        purchase_rewe_domain=purchase_rewe_domain,
                    )
                    if action == "created":
                        created_count += 1
                    elif action == "updated":
                        updated_count += 1

                total_receipts = purchase_domain.count_by_retailer(retailer_code)

        return PersistResult(
            created_count=created_count,
            updated_count=updated_count,
            total_receipts=total_receipts,
        )
