import json
from pathlib import Path


def test_frontend_api_codes_use_the_4xx_or_5xx_number_ranges():
    from api.errors import ApiErrorCode
    from api.services.dashboard_errors import (
        MISSING_DATABASE_ERROR_CODE,
        NO_RECEIPTS_ERROR_CODE,
    )
    from workflows.workflow_errors import (
        CONCURRENT_IMPORT_ERROR,
        DM_INITIAL_ERROR_DETAILS,
        LIDL_INITIAL_ERROR_DETAILS,
        ROSSMANN_INITIAL_ERROR_DETAILS,
        REWE_INITIAL_ERROR_DETAILS,
    )

    codes = [int(code) for code in ApiErrorCode]
    codes.extend([MISSING_DATABASE_ERROR_CODE, NO_RECEIPTS_ERROR_CODE])
    assert CONCURRENT_IMPORT_ERROR.error_code == int(ApiErrorCode.IMPORT_ALREADY_RUNNING)
    codes.extend(info.error_code for info in LIDL_INITIAL_ERROR_DETAILS.values())
    codes.extend(info.error_code for info in REWE_INITIAL_ERROR_DETAILS.values())
    codes.extend(info.error_code for info in DM_INITIAL_ERROR_DETAILS.values())
    codes.extend(info.error_code for info in ROSSMANN_INITIAL_ERROR_DETAILS.values())

    assert len(codes) == len(set(codes))
    assert all(4001 <= code <= 4099 or 5001 <= code <= 5099 for code in codes)
    catalog = json.loads(Path("web/src/locales/de.json").read_text())
    assert all(f"errors.api.{code}" in catalog for code in set(codes))


def test_http_error_status_maps_to_a_code_in_its_error_class():
    from api.errors import error_code_for_status

    assert 4001 <= int(error_code_for_status(404)) <= 4099
    assert 4001 <= int(error_code_for_status(422)) <= 4099
    assert 5001 <= int(error_code_for_status(503)) <= 5099
