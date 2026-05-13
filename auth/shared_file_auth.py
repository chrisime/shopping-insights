"""Shared helpers for file-based cookie loading."""

from __future__ import annotations

import simplejson
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional, Set

from requests import Session
from requests.cookies import create_cookie


def _default_cookie_sort_key(cookie: dict[str, Any]) -> tuple[str, str, str]:
    """Return the canonical sort key for normalized cookie dictionaries."""
    return (
        cookie.get("domain", ""),
        cookie.get("path", "/"),
        cookie.get("name", ""),
    )


@dataclass(frozen=True)
class CookieNameAnalysis:
    """Analysis of observed cookie names against required and recommended sets."""

    cookie_names: frozenset[str]
    missing_required: tuple[str, ...]
    present_recommended: tuple[str, ...]
    missing_recommended: tuple[str, ...]

    @property
    def has_any_recommended(self) -> bool:
        return bool(self.present_recommended)


# ---------------------------------------------------------------------------
# Store-agnostic diagnostic profile
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CookieDiagnosticProfile:
    """Store-specific texts for the shared cookie diagnostic output."""

    store_name: str
    required_cookies: Set[str]
    recommended_cookies: Set[str]

    # ROT
    rot_summary: str = "wahrscheinlich nicht ausreichend"
    rot_recommendation: str = ""
    rot_relogin_step: str = ""
    rot_missing_hint: str = ""

    # GELB
    gelb_summary: str = "brauchbar mit Risiko"
    gelb_recommendation: str = ""
    gelb_missing_hint: str = ""
    gelb_try_step: str = ""

    # GRUEN
    gruen_summary: str = "Datei wirkt direkt nutzbar"
    gruen_recommendation: str = ""
    gruen_step: str = ""

    # Missing-required diagnostic hint (printed inline)
    missing_required_hint: str = ""


@dataclass(frozen=True)
class CookieDiagnosticExtras:
    """Optional store-specific diagnostic lines and next steps."""

    lines: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)


def assess_cookie_quality(
    cookie_names: Set[str],
    profile: CookieDiagnosticProfile,
) -> tuple[str, str, str]:
    """Classify the current cookie set into an operational traffic-light rating."""
    if not profile.required_cookies.issubset(cookie_names):
        return "ROT", profile.rot_summary, profile.rot_recommendation

    if profile.recommended_cookies.issubset(cookie_names):
        return "GRUEN", profile.gruen_summary, profile.gruen_recommendation

    return "GELB", profile.gelb_summary, profile.gelb_recommendation


def print_cookie_diagnostics(
    cookie_jar,
    profile: CookieDiagnosticProfile,
    *,
    extras: Optional[CookieDiagnosticExtras] = None,
) -> None:
    """Print actionable diagnostics for a loaded cookie set."""
    analysis = analyze_cookie_names(
        (cookie.name for cookie in cookie_jar),
        required_cookies=profile.required_cookies,
        recommended_cookies=profile.recommended_cookies,
    )
    cookie_names = set(analysis.cookie_names)
    missing_required = sorted(analysis.missing_required)
    missing_recommended = sorted(analysis.missing_recommended)

    names = sorted(str(name) for name in cookie_names if name)
    cookie_names_list = ", ".join(names) if names else "keine"
    print(f"  Erkannte Cookie-Namen: {cookie_names_list}")

    if missing_required:
        print(
            f"⚠ Wichtige {profile.store_name}-Session-Cookies fehlen: {', '.join(missing_required)}"
        )
        if profile.missing_required_hint:
            print(f"  {profile.missing_required_hint}")

    if missing_recommended:
        print(
            f"⚠ Zusätzliche hilfreiche {profile.store_name}-Cookies fehlen: {', '.join(missing_recommended)}"
        )

    active_extras = extras or CookieDiagnosticExtras()
    for line in active_extras.lines:
        print(line)

    status, summary, recommendation = assess_cookie_quality(cookie_names, profile)
    print(f"  Ampelstatus: {status}")
    print(f"  Einschaetzung: {summary}")
    print(f"  Empfehlung: {recommendation}")
    steps = _build_next_steps(status, missing_required, missing_recommended, profile)
    steps.extend(active_extras.steps)
    for step in steps:
        print(f"  Naechster Schritt: {step}")


def _build_next_steps(
    status: str,
    missing_required: List[str],
    missing_recommended: List[str],
    profile: CookieDiagnosticProfile,
) -> List[str]:
    """Return concrete follow-up actions for the detected cookie-file quality."""
    steps: List[str] = []

    if status == "ROT":
        steps.append(profile.rot_relogin_step)
        if missing_required and profile.rot_missing_hint:
            steps.append(
                profile.rot_missing_hint.format(missing=', '.join(missing_required))
            )

    elif status == "GELB":
        if missing_recommended and profile.gelb_missing_hint:
            steps.append(
                profile.gelb_missing_hint.format(missing=', '.join(missing_recommended))
            )
        steps.append(profile.gelb_try_step)

    else:
        steps.append(profile.gruen_step)

    return steps


def parse_json_cookie_export(raw_cookie_text: str) -> Optional[list[dict]]:
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
    user_agent: Optional[str] = None,
    default_domain: str = "",
    domain_suffix: Optional[str] = None,
) -> tuple[Session, int]:
    """Create and populate a cookie-backed requests session."""
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


def analyze_cookie_names(
    cookie_names: Iterable[str],
    required_cookies: Iterable[str] = (),
    recommended_cookies: Iterable[str] = (),
) -> CookieNameAnalysis:
    """Analyze observed cookie names against required and recommended sets."""
    observed_names = frozenset(str(name) for name in cookie_names if name)
    required_set = set(required_cookies)
    recommended_set = set(recommended_cookies)
    return CookieNameAnalysis(
        cookie_names=observed_names,
        missing_required=tuple(sorted(required_set - observed_names)),
        present_recommended=tuple(sorted(recommended_set & observed_names)),
        missing_recommended=tuple(sorted(recommended_set - observed_names)),
    )


def _prepare_cookie_dicts(
    cookies_list: Iterable[dict[str, Any]],
    default_domain: str = "",
    domain_suffix: Optional[str] = None,
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


def _normalize_domain_suffix(domain_suffix: Optional[str]) -> Optional[str]:
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
