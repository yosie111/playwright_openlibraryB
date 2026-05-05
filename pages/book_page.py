from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage


class BookPage(BasePage):

    WANT_TO_READ_FORM = "form.reading-log.primary-action"
    WANT_TO_READ_BUTTON = f"{WANT_TO_READ_FORM} button.book-progress-btn"

    BUTTON_ACTIVATED = f"{WANT_TO_READ_BUTTON}.activated"
    BUTTON_UNACTIVATED = f"{WANT_TO_READ_BUTTON}.unactivated"

    async def goto(self, url: str) -> None:
        await self.page.goto(url)

    async def get_reading_status(self) -> str:
        try:
            await self.page.wait_for_function(
                f"""() => document.querySelector({self.BUTTON_ACTIVATED!r})
                    || document.querySelector({self.BUTTON_UNACTIVATED!r})""",
                timeout=5000,
            )
        except PlaywrightTimeoutError:
            return ""

        activated_el = await self.page.query_selector(self.BUTTON_ACTIVATED)
        if activated_el is not None:
            return "activated"

        unactivated_el = await self.page.query_selector(self.BUTTON_UNACTIVATED)
        if unactivated_el is not None:
            return "unactivated"

        return ""

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
        status = await self.get_reading_status()

        if status == "activated":
            return True

        await self.click_and_wait_for_state(self.BUTTON_ACTIVATED)

        status = await self.get_reading_status()
        return status == "activated"

    async def remove_from_reading_list(self) -> bool:
        status = await self.get_reading_status()

        if status == "unactivated":
            return True

        await self.click_and_wait_for_state(self.BUTTON_UNACTIVATED)

        status = await self.get_reading_status()
        return status == "unactivated"
