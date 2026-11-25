"""Serve the built dashboard and its precompressed assets."""

from pathlib import Path

from fastapi import FastAPI
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

FRONTEND_DIST = Path(__file__).resolve().parents[1] / "web" / "dist"
COMPRESSED_EXTENSIONS = {"br": ".br", "gzip": ".gz"}


def _accepted_encodings(headers: Headers) -> list[str]:
    qualities: dict[str, float] = {}
    for value in ",".join(headers.getlist("accept-encoding")).split(","):
        encoding, separator, parameter = value.lower().partition(";")
        name, _, weight = parameter.partition("=")
        if separator and name.strip() != "q":
            continue
        try:
            quality = float(weight) if separator else 1.0
        except ValueError:
            continue
        if 0 <= quality <= 1:
            qualities[encoding.strip()] = quality

    wildcard = qualities.get("*")
    weights = {
        encoding: qualities.get(encoding, wildcard or 0) for encoding in COMPRESSED_EXTENSIONS
    }
    weights["identity"] = qualities.get("identity", 0)
    encodings = sorted(
        (encoding for encoding, weight in weights.items() if weight > 0),
        key=weights.__getitem__,
        reverse=True,
    )
    # When allowed implicitly, identity comes after all accepted compressed variants.
    if "identity" not in qualities and wildcard != 0:
        encodings.append("identity")
    return encodings


class PrecompressedStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        original = await super().get_response(path, scope)
        if not path.endswith((".js", ".css")):
            return original

        response = original
        for encoding in _accepted_encodings(Headers(scope=scope)):
            if extension := COMPRESSED_EXTENSIONS.get(encoding):
                try:
                    response = await super().get_response(path + extension, scope)
                except HTTPException as exc:
                    if exc.status_code != 404:
                        raise
                    continue

                if response.status_code != 304:
                    response.headers["Content-Type"] = (
                        original.headers.get("content-type")
                        or FileResponse(path).headers["content-type"]
                    )
                    response.headers["Content-Encoding"] = encoding

            break
        else:
            response = Response(status_code=406)

        response.headers.add_vary_header("Accept-Encoding")
        return response


def register_frontend(app: FastAPI, directory: Path = FRONTEND_DIST) -> None:
    index = directory / "index.html"
    assets = directory / "assets"
    if not index.is_file() or not assets.is_dir():
        return

    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    async def dashboard_index() -> FileResponse:
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    app.mount("/assets", PrecompressedStaticFiles(directory=assets), name="frontend-assets")
