from config import BASE_URL, SCREENSHOTS_DIR
from pages.base_page import BasePage
from pages.book_page import BookPage
from pages.models import BookInfo
from utils import make_safe_filename


def books_needing_add(books: list[BookInfo]) -> list[BookInfo]:
    return [b for b in books if b.activated is not True]


class ReadingListPage(BasePage):

    PATH = "/account/books/want-to-read"
    LIST_ITEM_SELECTOR = ".searchResultItem"

    def __init__(self, page):
        super().__init__(page)
        self.results = self.LIST_ITEM_SELECTOR
        # Composition: per-book operations are delegated here.
        self.book_page = BookPage(page)

    # --- Operations on the /want-to-read listing itself ----------------

    async def goto(self):
        await self.page.goto(f"{BASE_URL}{self.PATH}")

    async def get_book_count(self) -> int:
        return await self.get_results_count()

    async def get_want_to_read_count(self, username: str) -> int:
        url = f"{BASE_URL}/people/{username}/books/want-to-read"
        await self.page.goto(url)
        return await self.get_book_count()

    
    
    async def assert_reading_list_count(
        self, username: str, expected_count: int
    ) -> None:
        actual = await self.get_want_to_read_count(username)
        assert actual == expected_count, (
            f"Expected {expected_count} books in {username}'s "
            f"want-to-read list, got {actual}"
        )

    async def add_books_to_reading_list(
        self,
        books: list[BookInfo]
        ) -> None:
        for info in books:
            await self.book_page.goto(info.url)
            status = await self.book_page.get_reading_status()
            if status == "activated":
                print(f"  Already in list: {info.url}")
            else:
                ok = await self.book_page.add_to_reading_list()
                if ok:
                    print(f"  Added to Want to Read: {info.url}")
                else:
                    print(f"  Add did not complete: {info.url}")

            safe_name = make_safe_filename(info.url)
            await self.page.screenshot(
                path=f"{SCREENSHOTS_DIR}/{safe_name}.png"
            )

    async def remove_books_from_reading_list(
        self, books: list[BookInfo]
    ) -> None:
        """Symmetric counterpart -- useful for cleanup and tests."""
        for info in books:
            await self.book_page.goto(info.url)
            try:
                ok = await self.book_page.remove_from_reading_list()
                if ok:
                    print(f"  Removed: {info.url}")
                else:
                    print(f"  Remove did not complete: {info.url}")
            except Exception as exc:
                print(
                    f"  WARN: remove may not have completed cleanly "
                    f"for {info.url} ({exc})"
                )
