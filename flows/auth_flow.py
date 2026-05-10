import json
import os
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from config import STORAGE_STATE_PATH
from pages import LoginPage, SessionPage


# Wait until either the "logged in" icon or the "login" link is rendered.
# Without this, is_logged_in() races the JS render and returns None even when
# the saved cookies are valid — forcing a fresh login on every run.
async def _wait_for_auth_indicator(page, timeout: int = 5000) -> None:
    try:
        await page.wait_for_selector(
            "img.account__icon, li.login-links",
            timeout=timeout,
        )
    except PlaywrightTimeoutError:
        # Page didn't settle in time; let is_logged_in() decide anyway.
        pass


async def login_if_needed(page):
    """Ensure the user is logged in. Returns username or None on failure."""
    await _wait_for_auth_indicator(page)

    session_page = SessionPage(page)
    username = await session_page.is_logged_in()
    if username:
        return username

    login_page = LoginPage(page)
    await login_page.goto()
    await login_page.login(
        os.environ.get("OPENLIBRARY_EMAIL"),
        os.environ.get("OPENLIBRARY_PASSWORD"),
    )

    username = await session_page.is_logged_in()
    if username:
        print(f"Successfully logged in as {username}")
        # Save session for future runs
        await page.context.storage_state(path=STORAGE_STATE_PATH)
        print(f"Session saved to {STORAGE_STATE_PATH}")
    else:
        print("Login failed: check credentials and try again.")
    return username


async def load_saved_session(context) -> bool:
    """Load cookies from storage_state.json into the context, if it exists."""
    path = Path(STORAGE_STATE_PATH)
    if not path.exists():
        return False

    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)

    cookies = state.get("cookies", [])
    if cookies:
        await context.add_cookies(cookies)
        print(f"Loaded {len(cookies)} cookies from {STORAGE_STATE_PATH}")
        return True
    return False
