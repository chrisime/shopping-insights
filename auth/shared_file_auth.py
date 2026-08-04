"""Shared helpers for file-based cookie loading.

Cookie diagnostics (traffic-light quality assessment) live in
:mod:`auth.cookie_diagnostics`; this module only builds sessions from
cookie data and reads cookie files.
"""

from __future__ import annotations

import simplejson
from pathlib import Path
from typing import Any, Iterable

from requests import Session
from requests.cookies import create_cookie


def _default_cookie_sort_key(cookie: dict[str, Any]) -> tuple[str, str, str]:
    """Return the canonical sort key for normalized cookie dictionaries."""
    return (
        cookie.get("domain", ""),
        cookie.get("path", "/"),
        cookie.get("name", ""),
    )


def parse_json_cookie_export(raw_cookie_text: str) -> list[dict] | None:
    """Parse common JSON cookie-export formats.

    Returns:
        list[dict]: Parsed cookie dicts when the text is valid JSON.
        []: Valid JSON, but not in a supported cookie-export shape.
        None: Not JSON at all.
    """
    try:
        cookies_data = simplejson.loads(raw_cookie_text)
    except simplejson.JSONDecodeError:
        return None

    if isinstance(cookies_data, dict) and "cookies" in cookies_data:
        cookies_list = cookies_data["cookies"]
    elif isinstance(cookies_data, list):
        cookies_list = cookies_data
    else:
        return []

    return [cookie for cookie in cookies_list if isinstance(cookie, dict)]


def read_utf8_text_file(file_path: str) -> str:
    """Read a UTF-8 encoded text file."""
    return Path(file_path).read_text(encoding="utf-8")


def build_cookie_session(
    cookies_list: Iterable[dict[str, Any]],
    user_agent: str | None = None,
    default_domain: str = "",
    domain_suffix: str | None = None,
    use_cloudscraper: bool = False,
) -> tuple[Session, int]:
    """Create and populate a cookie-backed requests session.

    When *use_cloudscraper* is True the session is created via
    ``cloudscraper.create_scraper()`` to bypass Cloudflare challenges.
    """
    if use_cloudscraper:
        import cloudscraper
        session = cloudscraper.create_scraper()
    else:
        session = Session()

    if user_agent:
        session.headers.update({"User-Agent": user_agent})

    normalized_cookies = _prepare_cookie_dicts(
        cookies_list,
        default_domain=default_domain,
        domain_suffix=domain_suffix,
    )
    _store_cookies_in_session(session, normalized_cookies)

    return session, len(normalized_cookies)


def _prepare_cookie_dicts(
    cookies_list: Iterable[dict[str, Any]],
    default_domain: str = "",
    domain_suffix: str | None = None,
) -> list[dict[str, Any]]:
    """Filter, normalize, deduplicate and sort cookie dictionaries."""
    deduplicated: dict[tuple[str, str, str], dict[str, Any]] = {}
    normalized_domain_suffix = _normalize_domain_suffix(domain_suffix)

    for cookie_data in cookies_list:
        normalized = _normalize_cookie_dict(cookie_data, default_domain)
        if normalized is None:
            continue
        if normalized_domain_suffix and not _matches_domain_suffix(normalized, normalized_domain_suffix):
            continue

        cookie_key = (
            str(normalized["domain"]),
            str(normalized["path"]),
            str(normalized["name"]),
        )
        deduplicated[cookie_key] = normalized

    normalized_cookies = list(deduplicated.values())
    normalized_cookies.sort(key=_default_cookie_sort_key)

    return normalized_cookies


def _normalize_domain_suffix(domain_suffix: str | None) -> str | None:
    """Normalize an optional cookie domain suffix for endswith matching."""
    if not domain_suffix:
        return None
    return domain_suffix.lower().lstrip(".")


def _matches_domain_suffix(cookie_data: dict[str, Any], domain_suffix: str) -> bool:
    """Return True when the cookie belongs to the requested domain suffix."""
    normalized_domain = str(cookie_data.get("domain", "")).lower().lstrip(".")
    return normalized_domain.endswith(domain_suffix)


def _normalize_cookie_dict(cookie_data: dict[str, Any], default_domain: str = "") -> dict[str, Any] | None:
    """Return a normalized cookie dictionary or None when required fields are missing."""
    domain = str(cookie_data.get("domain", default_domain) or default_domain)
    name = str(cookie_data.get("name", "") or "")
    if not domain or not name:
        return None

    return {
        "domain": domain,
        "name": name,
        "value": cookie_data.get("value", ""),
        "path": str(cookie_data.get("path", "/") or "/"),
        "secure": bool(cookie_data.get("secure", False)),
        "expirationDate": cookie_data.get("expirationDate"),
    }


def _store_cookies_in_session(session: Session, cookies_list: Iterable[dict[str, Any]]) -> None:
    """Write normalized cookie dictionaries into the target session."""
    for cookie_data in cookies_list:
        session.cookies.set_cookie(
            create_cookie(
                domain=str(cookie_data["domain"]),
                name=str(cookie_data["name"]),
                value=str(cookie_data.get("value", "")),
                path=str(cookie_data.get("path", "/")),
                secure=bool(cookie_data.get("secure", False)),
                expires=cookie_data.get("expirationDate"),
            )
        )
