"""Export adapters for generating external receipt formats from persisted DB data."""

from .json_export import export_receipts_from_db

__all__ = ["export_receipts_from_db"]

