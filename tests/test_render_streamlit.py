from frontend.ui_model import DashboardPageModel, DashboardSection


def test_render_dashboard_page_model_uses_streamlit_primitives():
    from frontend.render_streamlit import render_dashboard_page_model

    class FakeColumn:
        def __init__(self, calls):
            self.calls = calls

        def metric(self, label, value):
            self.calls.append(("metric", label, value))

        def bar_chart(self, data):
            self.calls.append(("bar_chart", list(data.index), list(data.values)))

    class FakeSt:
        def __init__(self):
            self.calls = []

        def title(self, text):
            self.calls.append(("title", text))

        def markdown(self, text, unsafe_allow_html=False):
            self.calls.append(("markdown", text))

        def columns(self, count):
            self.calls.append(("columns", count))
            return [FakeColumn(self.calls) for _ in range(count)]

        def bar_chart(self, data):
            self.calls.append(("bar_chart", list(data.index), list(data.values)))

        def dataframe(self, data, width=None, hide_index=False):
            self.calls.append(("dataframe", list(data.columns), hide_index))

        def info(self, text):
            self.calls.append(("info", text))

    page = DashboardPageModel(
        title="Shopping Analyzer Dashboard",
        sections=[
            DashboardSection(
                kind="metrics",
                title="Kennzahlen",
                items=[{"label": "A", "value": "1"}, {"label": "B", "value": "2"}],
            ),
            DashboardSection(
                kind="chart",
                title="Ausgaben über Zeit",
                items=[{"Zeitraum": "2024-01", "Ausgaben (€)": 10.0}],
            ),
            DashboardSection(
                kind="chart",
                title="Einkaufsverhalten nach Wochentag",
                items=[{"Wochentag": "Montag", "Einkäufe": 2, "Ø Ausgaben (€)": 3.0}],
            ),
            DashboardSection(
                kind="table",
                title="Top-Artikel",
                items=[{"Artikel": "Apfel", "Gesamtmenge": "2 pc", "Ausgaben (€)": 4.0, "Einkäufe": 1}],
            ),
        ],
    )

    fake_st = FakeSt()
    render_dashboard_page_model(page, st_module=fake_st)

    assert ("title", "Shopping Analyzer Dashboard") in fake_st.calls
    assert ("metric", "A", "1") in fake_st.calls
    assert any(call[0] == "bar_chart" for call in fake_st.calls)
    assert any(call[0] == "dataframe" for call in fake_st.calls)
