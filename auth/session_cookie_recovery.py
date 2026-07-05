"""Read session-only cookies from Firefox/LibreWolf session-restore files.

Firefox stores session cookies (those without an expiry) only in memory while
running. However, the session-restore mechanism persists them inside
``recovery.jsonlz4`` (in ``sessionstore-backups/``).  This module reads that
file so that important session-only cookies like REWE's ``rstp`` can be
recovered even though they never appear in ``cookies.sqlite``.

The file format is *mozLz4* – an 8-byte magic header (``mozLz40\0``) followed
by LZ4-block-compressed JSON.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import simplejson
import platform
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


def _find_firefox_profiles_dir(browser: str) -> Optional[Path]:
    """Return the ``Profiles`` directory for *firefox* or *librewolf*."""
    system = platform.system()
    home = Path.home()

    if system == "Darwin":
        roots = {
            "firefox": home / "Library" / "Application Support" / "Firefox" / "Profiles",
            "librewolf": home / "Library" / "Application Support" / "LibreWolf" / "Profiles",
        }
    elif system == "Linux":
        roots = {
            "firefox": home / ".mozilla" / "firefox",
            "librewolf": home / ".librewolf",
        }
    elif system == "Windows":
        appdata = Path.home() / "AppData" / "Roaming"
        roots = {
            "firefox": appdata / "Mozilla" / "Firefox" / "Profiles",
            "librewolf": appdata / "LibreWolf" / "Profiles",
        }
    else:
        return None

    return roots.get(browser)


def _find_default_profile(profiles_dir: Path) -> Optional[Path]:
    """Heuristic: pick the profile directory with a ``cookies.sqlite``."""
    if not profiles_dir.is_dir():
        return None

    candidates = [
        p.parent
        for p in profiles_dir.rglob("cookies.sqlite")
        if ".bkp" not in str(p)
    ]
    if not candidates:
        # Fallback: accept backup profiles too
        candidates = [p.parent for p in profiles_dir.rglob("cookies.sqlite")]

    # Prefer default-default, default-release or *.default profiles
    for c in candidates:
        if any(name in c.name for name in ("default-default", "default-release", ".default")):
            return c
    return candidates[0] if candidates else None


def _read_jsonlz4(path: Path) -> Optional[dict]:
    """Read a mozLz4 compressed JSON file."""
    try:
        import lz4.block  # noqa: WPS433 – optional at import-time
    except ImportError:
        return None

    try:
        raw = path.read_bytes()
    except OSError:
        return None

    # mozLz4 magic: b"mozLz40\0" (8 bytes)
    if not raw[:8] == b"mozLz40\0":
        return None

    try:
        decompressed = lz4.block.decompress(raw[8:])
        return simplejson.loads(decompressed)
    except Exception:
        return None


def read_session_cookies_for_domain(
    browser: str,
    domain_suffix: str,
) -> List[Dict]:
    """Return session cookies for *domain_suffix* from the session-restore file.

    Returns a list of dicts compatible with the ``cookie_data`` format used
    by :func:`shared_file_auth.build_cookie_session` / ``browser_cookie3``
    cookies (keys: ``domain``, ``name``, ``value``, ``path``, ``secure``).

    Returns an empty list when the file is missing, unreadable, or contains
    no matching cookies.
    """
    profiles_dir = _find_firefox_profiles_dir(browser)
    if profiles_dir is None:
        return []

    profile = _find_default_profile(profiles_dir)
    if profile is None:
        return []

    recovery = profile / "sessionstore-backups" / "recovery.jsonlz4"
    if not recovery.exists():
        return []

    data = _read_jsonlz4(recovery)
    if data is None:
        return []

    # Session cookies live under data["cookies"] (top-level list) and
    # possibly under each window's "cookies" key.
    raw_cookies: List[dict] = list(data.get("cookies", []))
    for window in data.get("windows", []):
        raw_cookies.extend(window.get("cookies", []))

    if not raw_cookies:
        return []

    domain_suffix_dot = f".{domain_suffix}"
    result: List[Dict] = []
    for c in raw_cookies:
        host = c.get("host", "")
        if not (host == domain_suffix or host.endswith(domain_suffix_dot)):
            continue
        result.append({
            "domain": host,
            "name": c.get("name", ""),
            "value": c.get("value", ""),
            "path": c.get("path", "/"),
            "secure": bool(c.get("secure", False)),
        })

    logger.info("  ℹ %d Session-Cookie(s) für %s aus Session-Restore gefunden", len(result), domain_suffix)
    return result


def _read_pref_value(
    prefs_js: Path, pref_name: str,
) -> Optional[str]:
    """Read a single pref value from a Firefox/LibreWolf ``prefs.js`` file.

    Returns the value as a string (e.g. ``"0"``, ``"2"``) or ``None`` if
    the pref is not found or the file is unreadable.
    """
    try:
        text = prefs_js.read_text("utf-8")
    except OSError:
        return None

    import re
    # Matches: user_pref("browser.sessionstore.privacy_level", 2);
    pattern = re.compile(
        rf'user_pref\(\s*"{re.escape(pref_name)}"\s*,\s*(.+?)\s*\)\s*;'
    )
    match = pattern.search(text)
    if match:
        return match.group(1).strip().strip('"')
    return None


def check_sessionstore_privacy_level(browser: str) -> Optional[bool]:
    """Check if the browser's ``browser.sessionstore.privacy_level`` is set
    to 2, which prevents session cookies from being saved to the session-
    restore file.

    Works for both Firefox and LibreWolf.

    Returns:
        ``True`` if privacy_level is 0 or 1 (session cookies OK).
        ``False`` if privacy_level is 2 (session cookies blocked).
        ``None`` if the check could not be performed (browser not found,
               profile missing, or prefs.js unreadable).
    """
    profiles_dir = _find_firefox_profiles_dir(browser)
    if profiles_dir is None:
        return None

    profile = _find_default_profile(profiles_dir)
    if profile is None:
        return None

    prefs_js = profile / "prefs.js"
    if not prefs_js.exists():
        return None

    value = _read_pref_value(prefs_js, "browser.sessionstore.privacy_level")
    if value is None:
        # Pref not set — defaults to 1 (Firefox) or 2 (LibreWolf)
        return None

    try:
        level = int(value)
    except (ValueError, TypeError):
        return None

    if level == 2:
        return False
    return True
