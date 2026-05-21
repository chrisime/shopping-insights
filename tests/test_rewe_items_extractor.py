"""Tests for parsing.rewe_items_extractor – pending-item pattern & Handeingabe."""

from parsing.rewe_items_extractor import extract_rewe_receipt_items


def _make_lines(*body_lines: str) -> list[str]:
    """Wrap body lines with the expected EUR header and separator."""
    return ["REWE", "Musterstr. 1", "EUR", *body_lines, "------", "SUMME EUR 10,00"]


class TestPendingItemPattern:
    def test_simple_item(self):
        lines = _make_lines("Vollmilch 3,5% 1,19 A")
        result = extract_rewe_receipt_items(lines)
        assert len(result.items) == 1
        assert result.items[0]["name"] == "Vollmilch 3,5%"
        assert result.items[0]["price"] == "1,19"
        assert result.items[0]["quantity"] == 1
        assert result.items[0]["unit"] == "stk"

    def test_item_with_quantity(self):
        lines = _make_lines(
            "Bio Bananen 0,78 A",
            "2 Stk x 0,39",
        )
        result = extract_rewe_receipt_items(lines)
        assert len(result.items) == 1
        assert result.items[0]["name"] == "Bio Bananen"
        assert result.items[0]["price"] == "0,39"
        assert result.items[0]["quantity"] == 2
        assert result.items[0]["unit"] == "stk"

    def test_item_with_weight(self):
        lines = _make_lines(
            "Tomaten Rispe 2,21 A",
            "0,552 kg x 4,00 EUR/kg",
        )
        result = extract_rewe_receipt_items(lines)
        assert len(result.items) == 1
        assert result.items[0]["name"] == "Tomaten Rispe"
        assert result.items[0]["price"] == "4,00"
        assert result.items[0]["quantity"] == 0.552
        assert result.items[0]["unit"] == "kg"

    def test_multiple_items_committed_in_order(self):
        lines = _make_lines(
            "Butter 2,49 A",
            "Milch 1,09 A",
            "Brot 3,29 B",
        )
        result = extract_rewe_receipt_items(lines)
        assert len(result.items) == 3
        assert result.items[0]["name"] == "Butter"
        assert result.items[1]["name"] == "Milch"
        assert result.items[2]["name"] == "Brot"

    def test_discount_item_tracked_as_saved(self):
        lines = _make_lines(
            "Joghurt 0,99 A",
            "RABATT -0,20 A",
        )
        result = extract_rewe_receipt_items(lines)
        assert len(result.items) == 1
        assert result.items[0]["name"] == "Joghurt"
        assert result.saved_amount == 0.20

    def test_deposit_return_tracked_separately(self):
        lines = _make_lines(
            "LEERGUT Pfand -0,25 A",
        )
        result = extract_rewe_receipt_items(lines)
        assert len(result.items) == 0
        assert result.saved_deposit == 0.25
        assert result.saved_amount == 0.0


class TestHandeingabe:
    def test_handeingabe_sets_weight_and_unit_price(self):
        lines = _make_lines(
            "Bananen 1,68 A",
            "Handeingabe E-Bon 0,422 kg",
        )
        result = extract_rewe_receipt_items(lines)
        assert len(result.items) == 1
        item = result.items[0]
        assert item["name"] == "Bananen"
        assert item["unit"] == "kg"
        assert abs(item["quantity"] - 0.422) < 0.001
        # unit_price = 1.68 / 0.422 ≈ 3.98
        unit_price_float = float(item["price"].replace(",", "."))
        assert abs(unit_price_float - 3.98) < 0.01

    def test_handeingabe_without_pending_is_ignored(self):
        lines = _make_lines(
            "Handeingabe E-Bon 0,500 kg",
            "Aepfel 2,00 A",
        )
        result = extract_rewe_receipt_items(lines)
        # Handeingabe before any item line is ignored; only Aepfel parsed
        assert len(result.items) == 1
        assert result.items[0]["name"] == "Aepfel"

    def test_handeingabe_followed_by_another_item(self):
        lines = _make_lines(
            "Bananen 1,68 A",
            "Handeingabe E-Bon 0,422 kg",
            "Milch 1,09 A",
        )
        result = extract_rewe_receipt_items(lines)
        assert len(result.items) == 2
        assert result.items[0]["name"] == "Bananen"
        assert result.items[0]["unit"] == "kg"
        assert result.items[1]["name"] == "Milch"
        assert result.items[1]["unit"] == "stk"

