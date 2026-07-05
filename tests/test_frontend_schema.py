def test_vue_dashboard_schema_roundtrip():
    from frontend.schema import VueDashboardPayload

    payload = VueDashboardPayload(
        title="Shopping Analyzer Dashboard",
        sections=[
            {
                "kind": "metrics",
                "title": "Kennzahlen",
                "items": [{"label": "Ausgaben gesamt", "value": "€10.00"}],
            }
        ],
    )

    data = payload.to_dict()
    restored = VueDashboardPayload.from_dict(data)

    assert data == {
        "title": "Shopping Analyzer Dashboard",
        "sections": [
            {
                "kind": "metrics",
                "title": "Kennzahlen",
                "items": [{"label": "Ausgaben gesamt", "value": "€10.00"}],
            }
        ],
    }
    assert restored == payload


def test_vue_dashboard_schema_json_roundtrip():
    from frontend.schema import VueDashboardPayload

    payload = VueDashboardPayload(title="Shopping Analyzer Dashboard", sections=[])

    data = payload.to_json()
    restored = VueDashboardPayload.from_json(data)

    assert '"title": "Shopping Analyzer Dashboard"' in data
    assert restored == payload
