"""Shared helpers for file-based cookie loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Set

import requests


CookiePredicate = Callable[[dict], bool]


@dataclass(frozen=True)
class CookieValidationResult:
    """Result of validating observed cookie names against a policy."""

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


def assess_cookie_quality(
    cookie_names: Set[str],
    profile: CookieDiagnosticProfile,
) -> tuple[str, str, str]:
    """Classify the current cookie set into an operational traffic-light rating."""
    if not profile.required_cookies.issubset(cookie_names):
        return ("ROT", profile.rot_summary, profile.rot_recommendation)

    if profile.recommended_cookies.issubset(cookie_names):
        return ("GRUEN", profile.gruen_summary, profile.gruen_recommendation)

    return ("GELB", profile.gelb_summary, profile.gelb_recommendation)


def print_cookie_diagnostics(
    cookie_jar,
    profile: CookieDiagnosticProfile,
    *,
    extra_diagnostics: Optional[Callable[[Set[str]], None]] = None,
    extra_steps: Optional[Callable[[str, Set[str]], List[str]]] = None,
) -> None:
    """Print actionable diagnostics for a loaded cookie set.

    Args:
        extra_diagnostics: Optional callback printing store-specific info lines.
        extra_steps: Optional callback returning additional next-step strings.
            Receives (status, cookie_names) and returns a list of step texts.
    """
    validation = validate_cookie_names(
        (cookie.name for cookie in cookie_jar),
        required_cookies=profile.required_cookies,
        recommended_cookies=profile.recommended_cookies,
    )
    cookie_names = set(validation.cookie_names)
    missing_required = sorted(validation.missing_required)
    missing_recommended = sorted(validation.missing_recommended)

    print(f"  Erkannte Cookie-Namen: {render_cookie_name_list(cookie_names)}")

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

    if extra_diagnostics:
        extra_diagnostics(cookie_names)

    status, summary, recommendation = assess_cookie_quality(cookie_names, profile)
    print(f"  Ampelstatus: {status}")
    print(f"  Einschaetzung: {summary}")
    print(f"  Empfehlung: {recommendation}")
    steps = build_next_steps(status, missing_required, missing_recommended, profile)
    if extra_steps:
        steps.extend(extra_steps(status, cookie_names))
    for step in steps:
        print(f"  Naechster Schritt: {step}")


def build_next_steps(
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
        cookies_data = json.loads(raw_cookie_text)
    except json.JSONDecodeError:
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


def create_cookie_session(user_agent: Optional[str] = None) -> requests.Session:
    """Create a requests session for cookie-based authentication."""
    session = requests.Session()
    if user_agent:
        session.headers.update({"User-Agent": user_agent})
    return session


def build_cookie_session(
    cookies_list: Iterable[dict],
    *,
    user_agent: Optional[str] = None,
    include_cookie: Optional[CookiePredicate] = None,
    default_domain: str = "",
    sort_key: Optional[Callable[[dict], object]] = None,
) -> tuple[requests.Session, int]:
    """Create and populate a cookie-backed requests session."""
    session = create_cookie_session(user_agent)
    cookie_count = add_cookie_dicts_to_session(
        session,
        cookies_list,
        include_cookie=include_cookie,
        default_domain=default_domain,
        sort_key=sort_key,
    )
    return session, cookie_count


def validate_cookie_names(
    cookie_names: Iterable[str],
    *,
    required_cookies: Iterable[str] = (),
    recommended_cookies: Iterable[str] = (),
) -> CookieValidationResult:
    """Validate observed cookie names against required and recommended sets."""
    observed_names = frozenset(str(name) for name in cookie_names if name)
    required_set = set(required_cookies)
    recommended_set = set(recommended_cookies)
    missing_recommended = tuple(sorted(recommended_set - observed_names))
    return CookieValidationResult(
        cookie_names=observed_names,
        missing_required=tuple(sorted(required_set - observed_names)),
        present_recommended=tuple(sorted(recommended_set & observed_names)),
        missing_recommended=missing_recommended,
    )


def classify_cookie_quality(validation: CookieValidationResult) -> str:
    """Classify validated cookies into ROT/GELB/GRUEN."""
    if validation.missing_required:
        return "ROT"
    if validation.missing_recommended:
        return "GELB"
    return "GRUEN"


def render_cookie_name_list(cookie_names: Iterable[str]) -> str:
    """Render cookie names in stable sorted order for diagnostics."""
    names = sorted(str(name) for name in cookie_names if name)
    return ", ".join(names) if names else "keine"


def add_cookie_dicts_to_session(
    session: requests.Session,
    cookies_list: Iterable[dict],
    *,
    include_cookie: Optional[CookiePredicate] = None,
    default_domain: str = "",
    sort_key: Optional[Callable[[dict], object]] = None,
) -> int:
    """Populate a session from cookie dictionaries with filtering and deduplication."""
    deduplicated: dict[tuple[str, str, str], dict] = {}
    for cookie_data in cookies_list:
        if include_cookie and not include_cookie(cookie_data):
            continue

        domain = str(cookie_data.get("domain", default_domain) or default_domain)
        name = str(cookie_data.get("name", "") or "")
        if not domain or not name:
            continue

        normalized = {
            "domain": domain,
            "name": name,
            "value": cookie_data.get("value", ""),
            "path": cookie_data.get("path", "/") or "/",
            "secure": bool(cookie_data.get("secure", False)),
            "expirationDate": cookie_data.get("expirationDate"),
        }
        deduplicated[(domain, normalized["path"], name)] = normalized

    normalized_cookies = list(deduplicated.values())
    if sort_key is not None:
        normalized_cookies.sort(key=sort_key)
    else:
        normalized_cookies.sort(
            key=lambda cookie: (
                cookie.get("domain", ""),
                cookie.get("path", "/"),
                cookie.get("name", ""),
            )
        )

    for cookie_data in normalized_cookies:
        session.cookies.set_cookie(
            requests.cookies.create_cookie(
                domain=cookie_data["domain"],
                name=cookie_data["name"],
                value=cookie_data.get("value", ""),
                path=cookie_data.get("path", "/"),
                secure=bool(cookie_data.get("secure", False)),
                expires=cookie_data.get("expirationDate"),
            )
        )
    return len(normalized_cookies)

