"""Configuration module for shopping analyzer."""

from .lidl_config import LidlConfig
from .rewe_config import ReweConfig
from .storage_config import SQLITE_RECEIPTS_DB_FILE

__all__ = [
	"LidlConfig",
	"ReweConfig",
	"SQLITE_RECEIPTS_DB_FILE",
]

