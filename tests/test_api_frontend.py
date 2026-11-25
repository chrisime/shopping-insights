from gzip import compress
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.frontend import register_frontend

SCRIPT = b"export default 42;\n"
GZIP_SCRIPT = compress(SCRIPT, mtime=0)
BROTLI_SCRIPT = bytes.fromhex("0b09806578706f72742064656661756c742034323b0a03")
ASSET_URL = "/assets/echarts-vendor-test.js"


@pytest.fixture
def frontend_client(tmp_path: Path) -> TestClient:
    assets = tmp_path / "assets"
    assets.mkdir()
    (tmp_path / "index.html").write_text("<div id='app'></div>")
    (assets / "echarts-vendor-test.js").write_bytes(SCRIPT)
    (assets / "echarts-vendor-test.js.br").write_bytes(BROTLI_SCRIPT)
    (assets / "echarts-vendor-test.js.gz").write_bytes(GZIP_SCRIPT)
    (assets / "gzip-only.js").write_bytes(SCRIPT)
    (assets / "gzip-only.js.gz").write_bytes(GZIP_SCRIPT)
    (assets / "orphan.js.br").write_bytes(BROTLI_SCRIPT)

    app = FastAPI()

    @app.get("/ui/dashboard")
    def dashboard():
        return {"title": "Dashboard"}

    register_frontend(app, tmp_path)
    return TestClient(app)


@pytest.mark.parametrize(
    ("accept_encoding", "encoding"),
    [
        ("gzip, br", "br"),
        ("br;q=0.5, gzip;q=1", "gzip"),
        ("br;q=0, gzip", "gzip"),
        ("br;q=0, *;q=0.5", "gzip"),
        ("br;q=0.5, identity;q=1", None),
        ("br;q=0, gzip;q=0", None),
        ("", None),
    ],
)
def test_serves_the_negotiated_asset(frontend_client, accept_encoding, encoding):
    identity = frontend_client.head(ASSET_URL, headers={"Accept-Encoding": "identity"})
    with frontend_client.stream(
        "GET", ASSET_URL, headers={"Accept-Encoding": accept_encoding}
    ) as response:
        assert response.status_code == 200
        assert response.headers["vary"] == "Accept-Encoding"
        assert "javascript" in response.headers["content-type"]
        assert response.headers["content-type"] == identity.headers["content-type"]
        assert response.headers.get("content-encoding") == encoding

        content = b"".join(response.iter_raw())
        assert content == {"br": BROTLI_SCRIPT, "gzip": GZIP_SCRIPT, None: SCRIPT}[encoding]
        assert len(content) == int(response.headers["content-length"])


def test_uses_gzip_when_the_brotli_sidecar_is_missing(frontend_client):
    response = frontend_client.get("/assets/gzip-only.js", headers={"Accept-Encoding": "br, gzip"})

    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
    assert response.content == SCRIPT


def test_returns_406_when_all_available_encodings_are_excluded(frontend_client):
    response = frontend_client.get(ASSET_URL, headers={"Accept-Encoding": "*;q=0"})

    assert response.status_code == 406
    assert response.headers["vary"] == "Accept-Encoding"


def test_head_and_conditional_requests_use_the_selected_variant(frontend_client):
    headers = {"Accept-Encoding": "br"}
    response = frontend_client.head(ASSET_URL, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "br"
    assert response.headers["content-length"] == str(len(BROTLI_SCRIPT))
    assert response.content == b""

    conditional = frontend_client.get(
        ASSET_URL, headers={**headers, "If-None-Match": response.headers["etag"]}
    )
    assert conditional.status_code == 304
    assert conditional.headers["vary"] == "Accept-Encoding"

    other_variant = frontend_client.get(
        ASSET_URL, headers={"Accept-Encoding": "gzip", "If-None-Match": response.headers["etag"]}
    )
    assert other_variant.status_code == 200
    assert other_variant.headers["content-encoding"] == "gzip"


def test_registers_the_dashboard_alongside_api_routes(frontend_client):
    index = frontend_client.get("/")
    assert index.status_code == 200
    assert index.headers["cache-control"] == "no-cache"
    assert index.text == "<div id='app'></div>"
    assert frontend_client.get("/ui/dashboard").json() == {"title": "Dashboard"}
    assert frontend_client.get("/assets/orphan.js", headers={"Accept-Encoding": "br"}).status_code == 404


def test_api_can_start_without_a_frontend_build(tmp_path):
    app = FastAPI()
    register_frontend(app, tmp_path)
    assert TestClient(app).get("/").status_code == 404
