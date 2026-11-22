"""Configuration module for shopping analyzer."""

from .dm_config import DmConfig
from .lidl_config import LidlConfig
from .rewe_config import ReweConfig
from .rossmann_config import RossmannConfig
from .storage_config import SQLITE_RECEIPTS_DB_FILE

__all__ = [
	"DmConfig",
	"LidlConfig",
	"ReweConfig",
	"RossmannConfig",
	"SQLITE_RECEIPTS_DB_FILE",
]

