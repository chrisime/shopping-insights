from pathlib import Path


def test_resolve_receipts_path_uses_retailer_defaults():
    from storage.receipt_repository import _resolve_receipts_path

    assert _resolve_receipts_path(None, "lidl") == Path("lidl_receipts.json")
    assert _resolve_receipts_path(None, "rewe") == Path("rewe_receipts.json")


def test_resolve_receipts_path_prefers_explicit_file_path():
    from storage.receipt_repository import _resolve_receipts_path

    assert _resolve_receipts_path("custom.json", "lidl") == Path("custom.json")
