from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from config import BASE_URL
from pages.base_page import BasePage
from pages.session_page import SessionPage


class LoginPage(BasePage):
    PATH = "/account/login"

    USERNAME_INPUT = "input#username"
    PASSWORD_INPUT = "input#password"
    SUBMIT_BUTTON = "button[name='login'][type='submit']"

    ERROR_MESSAGE = ".note-error, .invalid"

    def __init__(self, page):
        super().__init__(page)

        self.session = SessionPage(page)

    async def goto(self):
        await self.page.goto(f"{BASE_URL}{self.PATH}")

    async def login(self, email, password) -> bool:

        # Pre-check: already authenticated?
        if await self.session.is_logged_in():
            return True

        await self.page.fill(self.USERNAME_INPUT, email)
        await self.page.fill(self.PASSWORD_INPUT, password)

        try:
            async with self.page.expect_navigation(
                wait_until="networkidle", timeout=10000
            ):
                await self.page.click(self.SUBMIT_BUTTON)
        except PlaywrightTimeoutError:
            await self.page.wait_for_load_state("networkidle")

        # Post-check: did the session actually become authenticated?
        username = await self.session.is_logged_in()
        return username is not None

    async def get_error_message(self):
        el = await self.page.query_selector(self.ERROR_MESSAGE)
        if not el:
            return None
        text = await el.inner_text()
        return text.strip() or None
