"""Laufzeitnahe Händlerdaten für Storage-Ziele und Metadaten."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .lidl_config import LidlConfig
from .rewe_config import ReweConfig


@dataclass(frozen=True)
class RetailerRuntime:
    """Laufzeitdaten eines unterstützten Händlers."""

    code: str
    name: str
    country: str
    receipts_json_file: str


_RUNTIME_DEFINITIONS = {
    "lidl": {
        "name": "LIDL",
        "country_getter": LidlConfig.get_country_code,
        "receipts_json_file": LidlConfig.RECEIPTS_JSON_FILE,
    },
    "rewe": {
        "name": "REWE",
        "country_getter": ReweConfig.get_country_code,
        "receipts_json_file": ReweConfig.RECEIPTS_JSON_FILE,
    },
}



def get_retailer_runtime(retailer: str) -> Optional[RetailerRuntime]:
    retailer_code = retailer.strip().lower()
    if not retailer_code:
        return None

    definition = _RUNTIME_DEFINITIONS.get(retailer_code)
    if definition is None:
        return None

    return RetailerRuntime(
        code=retailer_code,
        name=definition["name"],
        country=definition["country_getter"](),
        receipts_json_file=definition["receipts_json_file"],
    )
