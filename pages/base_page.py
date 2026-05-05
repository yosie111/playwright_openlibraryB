from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from config import DEFAULT_TIMEOUT


class BasePage:
    def __init__(self, page):
        self.page = page
        self.results = None
        self.next_page_button = None

    async def fill_and_submit(self, input_selector, button_selector, value):
        await self.page.fill(input_selector, value)
        await self.page.click(button_selector)

    async def get_results(self):
        try:
            await self.page.wait_for_selector(self.results, timeout=DEFAULT_TIMEOUT)
            return await self.page.query_selector_all(self.results)
        except PlaywrightTimeoutError:
            return []

    async def get_results_count(self):
        results = await self.get_results()
        return len(results)

    async def go_to_next_page(self):
        next_btn = await self.page.query_selector(self.next_page_button)

        if next_btn:
            await next_btn.click()
            return True

        return False
