"""Shared logic for the Want-to-Read button state.

DOM structure on Open Library:
    <form class="reading-log primary-action">
        <button class="book-progress-btn primary-action activated">
        -- or --
        <button class="book-progress-btn primary-action unactivated">
"""
from typing import Optional

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# --- Selectors (single source of truth) ---------------------------------
READING_LOG_FORM = "form.reading-log.primary-action"
WANT_TO_READ_BUTTON = f"{READING_LOG_FORM} button.book-progress-btn"

# Selector inside a search-result card (no surrounding form there).
# Both states share these two classes; 'activated'/'unactivated' is added
# as a third class and is what `read_button_state` inspects.
WANT_TO_READ_BUTTON_IN_CARD = "button.book-progress-btn.primary-action"

# --- Class names --------------------------------------------------------
ACTIVATED_CLASS = "activated"
UNACTIVATED_CLASS = "unactivated"

# --- Status string values -----------------------------------------------
STATUS_ACTIVATED = "activated"
STATUS_UNACTIVATED = "unactivated"

STATUS_TO_BOOL = {
    STATUS_ACTIVATED: True,
    STATUS_UNACTIVATED: False,
}


async def read_button_state(btn) -> Optional[str]:
    """Read the state from a button handle by its class attribute.

    Works on any handle -- from a search card or a full book page.
    Returns 'activated' / 'unactivated' / None.
    """
    if btn is None:
        return None

    cls = (await btn.get_attribute("class") or "").split()
    if ACTIVATED_CLASS in cls:
        return STATUS_ACTIVATED
    if UNACTIVATED_CLASS in cls:
        return STATUS_UNACTIVATED
    return None


async def wait_for_stable_state(page, timeout: int = 5000) -> bool:
    """Wait until the button settles into activated/unactivated.

    Use on a full book page (after navigation or click) before reading
    the state. Returns True if settled in time, False on timeout.
    """
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
