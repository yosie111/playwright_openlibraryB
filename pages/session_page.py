import re
from typing import Optional

from pages.base_page import BasePage


class SessionPage(BasePage):

    ACCOUNT_ICON = "img.account__icon"
    LOGIN_LINKS = "li.login-links"

    # Match the @USERNAME suffix in the avatar URL.
    # Example src: https://archive.org/services/img/@yosi545433
    USERNAME_FROM_SRC = re.compile(r"/img/@([^/?#]+)")

    async def is_logged_in(self) -> Optional[str]:
        el = await self.page.query_selector(self.ACCOUNT_ICON)
        if not el:
            return None

        src = await el.get_attribute("src")
        if not src:
            return None

        m = self.USERNAME_FROM_SRC.search(src)
        return m.group(1) if m else None

    async def get_username(self) -> Optional[str]:
        return await self.is_logged_in()

    async def is_logged_out(self) -> Optional[str]:
        icon = await self.page.query_selector(self.ACCOUNT_ICON)
        if icon is not None:
            return None

        links = await self.page.query_selector(self.LOGIN_LINKS)
        if links is None:
            return None

        return "not connected"
