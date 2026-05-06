from typing import Optional

from pages.base_page import BasePage
from pages.reading_status import (
    ACTIVATED_CLASS,
    STATUS_ACTIVATED,
    STATUS_UNACTIVATED,
    UNACTIVATED_CLASS,
    WANT_TO_READ_BUTTON,
    read_button_state,
    wait_for_stable_state,
)


class BookPage(BasePage):
    # Reuse shared selectors.
    WANT_TO_READ_BUTTON = WANT_TO_READ_BUTTON
    BUTTON_ACTIVATED = f"{WANT_TO_READ_BUTTON}.{ACTIVATED_CLASS}"
    BUTTON_UNACTIVATED = f"{WANT_TO_READ_BUTTON}.{UNACTIVATED_CLASS}"

    async def goto(self, url: str) -> None:
        await self.page.goto(url)

    async def get_reading_status(self) -> Optional[str]:
        # Wait for stable state, then read it.
        if not await wait_for_stable_state(self.page):
            return None

        btn = await self.page.query_selector(self.WANT_TO_READ_BUTTON)
        return await read_button_state(btn)

    async def click_and_wait_for_state(self, expected_selector: str) -> None:
        async with self.page.expect_response(
            lambda r: "bookshelves.json" in r.url
            and r.request.method == "POST",
            timeout=10000,
        ):
            await self.page.click(self.WANT_TO_READ_BUTTON)

        await self.page.wait_for_selector(
            expected_selector,
            timeout=5000,
        )

    async def add_to_reading_list(self) -> bool:
        if await self.get_reading_status() == STATUS_ACTIVATED:
            return True

        await self.click_and_wait_for_state(self.BUTTON_ACTIVATED)
        return await self.get_reading_status() == STATUS_ACTIVATED

    async def remove_from_reading_list(self) -> bool:
        if await self.get_reading_status() == STATUS_UNACTIVATED:
            return True

        await self.click_and_wait_for_state(self.BUTTON_UNACTIVATED)
        return await self.get_reading_status() == STATUS_UNACTIVATED
