"""Configuration module for shopping analyzer."""

from .lidl_config import LidlConfig
from .receipt_schema_profiles import get_receipt_schema_profile
from .retailer_runtime import (
	RetailerRuntime,
	get_retailer_runtime,
)
from .rewe_config import ReweConfig
from .storage_config import SQLITE_RECEIPTS_DB_FILE

__all__ = [
	"LidlConfig",
	"ReweConfig",
	"RetailerRuntime",
	"SQLITE_RECEIPTS_DB_FILE",
	"get_receipt_schema_profile",
	"get_retailer_runtime",
]

