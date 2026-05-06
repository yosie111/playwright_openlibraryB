"""Helpers for Want-to-Read button state on page and search card DOM."""
from typing import Optional

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Shared selectors.
READING_LOG_FORM = "form.reading-log.primary-action"
WANT_TO_READ_BUTTON = f"{READING_LOG_FORM} button.book-progress-btn"

# Card button selector.
WANT_TO_READ_BUTTON_IN_CARD = "button.book-progress-btn.primary-action"

# Status classes.
ACTIVATED_CLASS = "activated"
UNACTIVATED_CLASS = "unactivated"

# Status values.
STATUS_ACTIVATED = "activated"
STATUS_UNACTIVATED = "unactivated"

STATUS_TO_BOOL = {
    STATUS_ACTIVATED: True,
    STATUS_UNACTIVATED: False,
}


async def read_button_state(btn) -> Optional[str]:
    """Return state from card or book-page button: activated/unactivated/None."""
    if btn is None:
        return None

    cls = (await btn.get_attribute("class") or "").split()
    if ACTIVATED_CLASS in cls:
        return STATUS_ACTIVATED
    if UNACTIVATED_CLASS in cls:
        return STATUS_UNACTIVATED
    return None


async def wait_for_stable_state(page, timeout: int = 5000) -> bool:
    """Wait for activated/unactivated state. False on timeout."""
    js = f"""() => {{
        const el = document.querySelector('{WANT_TO_READ_BUTTON}');
        if (!el) return false;
        return el.classList.contains('{ACTIVATED_CLASS}')
            || el.classList.contains('{UNACTIVATED_CLASS}');
    }}"""
    try:
        await page.wait_for_function(js, timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False
