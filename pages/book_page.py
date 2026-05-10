from pages.base_page import BasePage
from pages.models import BOOKSHELF_WANT_TO_READ
from pages.reading_status import get_bookshelf_status


class BookPage(BasePage):
    # The primary reading-log form/button on the book page
    WANT_TO_READ_FORM = "form.reading-log.primary-action"
    WANT_TO_READ_BUTTON = f"{WANT_TO_READ_FORM} button.book-progress-btn"
    ACTION_INPUT_SELECTOR = (
        f"{WANT_TO_READ_FORM} input[name='action']"
    )

    async def goto(self, url: str) -> None:
        await self.page.goto(url)

    async def get_bookshelf_id(self) -> int:
        """Return the current bookshelf id for this book.

        Returns 1 (Want to Read), 2 (Currently Reading), 3 (Already Read),
        or -1 if the book is on no shelf.
        """
        await self.page.wait_for_selector(
            self.WANT_TO_READ_FORM, timeout=5000
        )
        return await get_bookshelf_status(self.page)

    async def _click_and_wait_for_action(self, expected_action: str) -> None:
        """Click the primary button and wait until the form's action flips.

        After clicking 'add', the form should switch to action='remove'
        (because clicking again would now remove). After 'remove', the
        form should switch to action='add'.
        """
        async with self.page.expect_response(
            lambda r: "bookshelves.json" in r.url
            and r.request.method == "POST",
            timeout=10000,
        ):
            await self.page.click(self.WANT_TO_READ_BUTTON)

        js = f"""() => {{
            const el = document.querySelector("{self.ACTION_INPUT_SELECTOR}");
            return el && el.value === "{expected_action}";
        }}"""
        await self.page.wait_for_function(js, timeout=5000)

    async def add_to_reading_list(self) -> bool:
        """Ensure the book is on Want-to-Read. Returns True on success."""
        if await self.get_bookshelf_id() == BOOKSHELF_WANT_TO_READ:
            return True

        # Once added, the form should flip to action='remove'
        await self._click_and_wait_for_action("remove")
        return await self.get_bookshelf_id() == BOOKSHELF_WANT_TO_READ

    async def remove_from_reading_list(self) -> bool:
        """Ensure the book is NOT on Want-to-Read. Returns True on success."""
        if await self.get_bookshelf_id() != BOOKSHELF_WANT_TO_READ:
            return True

        # Once removed, the form should flip to action='add'
        await self._click_and_wait_for_action("add")
        return await self.get_bookshelf_id() != BOOKSHELF_WANT_TO_READ
