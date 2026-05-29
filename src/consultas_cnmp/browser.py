"""Gerenciamento do contexto de browser (local ou Browserbase)."""

import os
from contextlib import contextmanager

from playwright.sync_api import Page, sync_playwright

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_STEALTH = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"


@contextmanager
def new_page(use_browserbase: bool = False) -> Page:
    """Context manager que entrega uma Page pronta para uso."""
    with sync_playwright() as p:
        if use_browserbase:
            browser, page = _browserbase_page(p)
        else:
            browser, page = _local_page(p)

        page.add_init_script(_STEALTH)
        try:
            yield page
        finally:
            browser.close()


def _local_page(p):
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(user_agent=_USER_AGENT)
    return browser, ctx.new_page()


def _browserbase_page(p):
    try:
        from browserbase import Browserbase
    except ImportError:
        raise ImportError(
            "Instale o extra: pip install 'consultas-cnmp[browserbase]'"
        )

    api_key = os.environ.get("BROWSERBASE_API_KEY", "")
    project_id = os.environ.get("BROWSERBASE_PROJECT_ID", "")
    if not api_key or not project_id:
        raise EnvironmentError(
            "Defina BROWSERBASE_API_KEY e BROWSERBASE_PROJECT_ID."
        )

    bb = Browserbase(api_key=api_key)
    session = bb.sessions.create(project_id=project_id)
    browser = p.chromium.connect_over_cdp(session.connect_url)
    return browser, browser.contexts[0].new_page()
