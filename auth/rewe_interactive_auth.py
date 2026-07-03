"""Interactive browser login for REWE with manual MFA and cookie handover."""

import time
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import requests

from config import ReweConfig


MACOS_BROWSER_BINARIES = {
    "firefox": [Path("/Applications/Firefox.app/Contents/MacOS/firefox")],
    "librewolf": [Path("/Applications/LibreWolf.app/Contents/MacOS/librewolf")],
    "chrome": [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")],
    "chromium": [Path("/Applications/Chromium.app/Contents/MacOS/Chromium")],
}


def load_rewe_cookies_from_interactive_browser(
    browser: str = "firefox",
    login_timeout: int = ReweConfig.INTERACTIVE_LOGIN_TIMEOUT,
) -> Optional[requests.Session]:
    """Open a visible browser, wait for manual login/MFA, then import the live cookies."""
    browser_name = ReweConfig.SUPPORTED_BROWSERS.get(browser, browser)

    try:
        driver = _create_driver(browser)
    except ImportError:
        print("✗ Selenium ist nicht installiert. Bitte installiere die Projekt-Abhaengigkeiten neu.")
        return None
    except Exception as exc:  # pragma: no cover - browser/OS dependent
        print(f"✗ Interaktiver Browser-Login konnte nicht gestartet werden: {exc}")
        return None

    try:
        print(f"Starte interaktiven REWE-Login in {browser_name}...")
        print("Bitte melde dich im geoefneten Browser bei REWE an und bestaetige deine MFA.")
        print("Lasse den Browser danach auf einer REWE-Seite geoeffnet, bis die Cookies uebernommen wurden.")

        driver.get(ReweConfig.get_mydata_receipts_url())
        if not _wait_for_rewe_session_cookie(driver, login_timeout):
            print("✗ Timeout beim interaktiven REWE-Login.")
            print(
                "Es wurde innerhalb des Zeitlimits kein rstp-Cookie im laufenden Browser-Kontext gefunden."
            )
            return None

        cookies = _collect_rewe_cookies(driver)
        if not cookies:
            print("✗ Nach dem interaktiven Login konnten keine REWE-Cookies aus dem Browser gelesen werden.")
            return None

        session = _build_requests_session(cookies)
        cookie_names = {cookie.name for cookie in session.cookies}
        if "rstp" not in cookie_names:
            print("✗ Der interaktive Browser-Kontext liefert weiterhin kein rstp-Cookie.")
            return None

        print(f"✓ Erfolgreich {len(session.cookies)} REWE-Cookies aus dem laufenden {browser_name}-Browser uebernommen")
        return session
    finally:
        driver.quit()


def _create_driver(browser: str):
    """Create a visible Selenium WebDriver for the selected browser."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions

    if browser in {"firefox", "librewolf"}:
        options = FirefoxOptions()
        options.headless = False
        binary_path = _find_browser_binary(browser)
        if binary_path:
            options.binary_location = str(binary_path)
        return webdriver.Firefox(options=options)

    if browser in {"chrome", "chromium"}:
        options = ChromeOptions()
        binary_path = _find_browser_binary(browser)
        if binary_path:
            options.binary_location = str(binary_path)
        return webdriver.Chrome(options=options)

    raise ValueError(f"Nicht unterstuetzter Browser fuer interaktiven Login: {browser}")


def _find_browser_binary(browser: str) -> Optional[Path]:
    """Return a known macOS browser binary path if available."""
    for candidate in MACOS_BROWSER_BINARIES.get(browser, []):
        if candidate.exists():
            return candidate
    return None


def _wait_for_rewe_session_cookie(driver, login_timeout: int) -> bool:
    """Poll the live browser context until the REWE session cookie appears."""
    deadline = time.time() + max(login_timeout, 1)
    last_url = ""
    while time.time() < deadline:
        try:
            last_url = driver.current_url
            cookies = driver.get_cookies()
        except Exception:
            time.sleep(2)
            continue

        cookie_names = {cookie.get("name") for cookie in cookies}
        if "rstp" in cookie_names and ReweConfig.COOKIE_DOMAIN in last_url:
            return True

        time.sleep(2)

    if last_url:
        print(f"Letzte beobachtete Browser-URL: {last_url}")
    return False


def _collect_rewe_cookies(driver) -> Iterable[dict]:
    """Collect cookies from the live browser context after successful login."""
    collected: Dict[Tuple[str, str, str], dict] = {}
    urls_to_visit = [
        driver.current_url,
        ReweConfig.BASE_URL,
        ReweConfig.get_mydata_receipts_url(),
    ]

    for url in urls_to_visit:
        if not url.startswith("http"):
            continue
        try:
            driver.get(url)
            time.sleep(1)
            for cookie in driver.get_cookies():
                domain = cookie.get("domain", "")
                if not domain.lower().lstrip(".").endswith(ReweConfig.COOKIE_DOMAIN):
                    continue
                key = (domain, cookie.get("name", ""), cookie.get("path", "/"))
                collected[key] = cookie
        except Exception:
            continue

    return list(collected.values())


def _build_requests_session(cookies: Iterable[dict]) -> requests.Session:
    """Convert Selenium-style cookie dicts into a requests session."""
    session = requests.Session()
    session.headers.update({"User-Agent": ReweConfig.DEFAULT_USER_AGENT})

    for cookie in cookies:
        session.cookies.set_cookie(
            requests.cookies.create_cookie(
                domain=cookie.get("domain", ""),
                name=cookie.get("name", ""),
                value=cookie.get("value", ""),
                secure=cookie.get("secure", False),
                path=cookie.get("path", "/"),
                expires=cookie.get("expiry"),
            )
        )

    return session

