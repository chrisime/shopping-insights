"""Cookie diagnostics — traffic-light quality assessment for loaded cookie sets.

Holds the store-agnostic diagnostic profile and output helpers; session
construction from cookies lives in :mod:`auth.shared_file_auth`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CookieNameAnalysis:
    """Analysis of observed cookie names against required and recommended sets."""

    cookie_names: frozenset[str]
    missing_required: tuple[str, ...]
    present_recommended: tuple[str, ...]
    missing_recommended: tuple[str, ...]


@dataclass(frozen=True)
class CookieDiagnosticProfile:
    """Store-specific texts for the shared cookie diagnostic output."""

    store_name: str
    required_cookies: set[str]
    recommended_cookies: set[str]

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
    cookie_names: set[str],
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
    extras: CookieDiagnosticExtras | None = None,
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
    logger.info("  Erkannte Cookie-Namen: %s", cookie_names_list)

    if missing_required:
        logger.warning("⚠ Wichtige %s-Session-Cookies fehlen: %s", profile.store_name, ", ".join(missing_required))
        if profile.missing_required_hint:
            logger.info("  %s", profile.missing_required_hint)

    if missing_recommended:
        logger.info("⚠ Zusätzliche hilfreiche %s-Cookies fehlen: %s", profile.store_name, ", ".join(missing_recommended))

    active_extras = extras or CookieDiagnosticExtras()
    for line in active_extras.lines:
        logger.info(line)

    status, summary, recommendation = assess_cookie_quality(cookie_names, profile)
    logger.info("  Ampelstatus: %s", status)
    logger.info("  Einschaetzung: %s", summary)
    logger.info("  Empfehlung: %s", recommendation)
    steps = _build_next_steps(status, missing_required, missing_recommended, profile)
    steps.extend(active_extras.steps)
    for step in steps:
        logger.info("  Naechster Schritt: %s", step)


def _build_next_steps(
    status: str,
    missing_required: list[str],
    missing_recommended: list[str],
    profile: CookieDiagnosticProfile,
) -> list[str]:
    """Return concrete follow-up actions for the detected cookie-file quality."""
    steps: list[str] = []

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
