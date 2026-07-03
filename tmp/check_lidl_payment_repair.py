import json
from collections import Counter
from pathlib import Path

from workflows.lidl_workflow import _needs_lidl_metadata_refresh

path = Path('/Users/christian.meyer/Repos/shopping-analyzer/lidl_receipts.json')
receipts = json.loads(path.read_text(encoding='utf-8'))


def bad_pm(pm):
    if not isinstance(pm, dict):
        return False
    return (
        pm.get('network') == ':'
        or str(pm.get('card_masked', '')).startswith(': ')
        or str(pm.get('details', '')).startswith(': ')
    )


bad = [r for r in receipts if any(bad_pm(pm) for pm in (r.get('payment_methods') or []))]
needs_refresh = [r for r in receipts if _needs_lidl_metadata_refresh(r)]

print('bad legacy payment_methods:', len(bad))
print('refresh-beduerftig nach aktueller Logik:', len(needs_refresh))
print('by year of bad entries:', Counter(str(r.get('purchase_date', ''))[:4] for r in bad))

for target in [
    '23000987220230701795843',
    '23000987120230629113587',
    '23005882820240625319782',
]:
    receipt = next((r for r in receipts if r.get('id') == target), None)
    print(
        target,
        receipt.get('payment_methods') if receipt else None,
        receipt.get('market') if receipt else None,
        receipt.get('register') if receipt else None,
        receipt.get('cashier') if receipt else None,
    )

