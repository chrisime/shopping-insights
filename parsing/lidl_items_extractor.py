"""Extract receipt items from HTML content."""

import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from shared.float_parser import parse_german_float

from shared.receipt_schema import build_receipt_item

logger = logging.getLogger(__name__)


def extract_lidl_receipt_items(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract items from a Lidl HTML receipt."""
    items = []
    try:
        # Find all article spans (they contain data-art-* attributes)
        article_spans = soup.find_all("span", class_="article")

        if not article_spans:
            logger.warning("Keine Artikel-Spans gefunden")
            return items

        # Group spans by article ID and description to handle duplicates
        # This handles cases where same article ID appears with different descriptions
        items_by_id_and_desc = {}
        for span in article_spans:
            art_id = span.get("data-art-id")
            art_description = span.get("data-art-description", "")
            if art_id and art_description:
                key = f"{art_id}_{art_description}"
                if key not in items_by_id_and_desc:
                    items_by_id_and_desc[key] = []
                items_by_id_and_desc[key].append(span)

        # Process each article
        for art_id_and_desc, spans in items_by_id_and_desc.items():
            try:
                # Get the first span (should contain all the data attributes)
                main_span = spans[0]

                # Extract item details from data attributes
                art_description = main_span.get("data-art-description", "")
                art_quantity = main_span.get("data-art-quantity", "1")
                unit_price = main_span.get("data-unit-price", "")

                if not art_description or not unit_price:
                    continue

                # Determine unit (kg or stk) from text content
                unit = "stk"
                for span in spans:
                    span_text = span.get_text()
                    if "kg" in span_text or "EUR/kg" in span_text:
                        unit = "kg"
                        break

                price = parse_german_float(unit_price) or 0.0

                items.append(
                    build_receipt_item(
                        name=art_description,
                        price=price,
                        quantity=art_quantity,
                        unit=unit,
                    )
                )

            except Exception as e:
                logger.warning("Fehler beim Extrahieren eines Artikels: %s", e)

    except Exception as e:
        logger.warning("Artikel nicht gefunden: %s", e)

    return items
