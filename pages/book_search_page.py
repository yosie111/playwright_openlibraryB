import re
from typing import Optional

from config import BASE_URL
from pages.base_page import BasePage
from pages.book_page import BookPage
from pages.models import BookInfo


class BookSearchPage(BasePage):

    SEARCH_BAR_SELECTOR = ".search-bar"
    RESULTS_SELECTOR = ".searchResultItem"
    NEXT_PAGE_SELECTOR = "ol-pagination a[aria-label='Go to next page']"
    LINK_SELECTOR = ".booktitle a"
    WANT_TO_READ_BTN = "button.book-progress-btn"
    _STATUS_TO_BOOL = {"activated": True, "unactivated": False}

    def __init__(self, page):
        super().__init__(page)

        self.search_input = (
            f"{self.SEARCH_BAR_SELECTOR} form input[name='q'][type='text']"
        )
        self.search_button = (
            f"{self.SEARCH_BAR_SELECTOR} form "
            f"input[type='submit'].search-bar-submit"
        )
        self.results = self.RESULTS_SELECTOR
        self.next_page_button = self.NEXT_PAGE_SELECTOR
        self.book_page = BookPage(page)

    async def search(self, query):
        await self.fill_and_submit(
            self.search_input,
            self.search_button,
            query,
        )

    async def extract_reading_status(self, item) -> Optional[str]:
        btn = await item.query_selector(self.WANT_TO_READ_BTN)
        if btn is None:
            return None

        cls = await btn.get_attribute("class") or ""
        classes = cls.split()
        if "activated" in classes:
            return "activated"
        if "unactivated" in classes:
            return "unactivated"
        return None

    async def extract_card_info(self, item) -> Optional[BookInfo]:
        text = await item.inner_text()

        match = re.search(r"First published in\s+(\d{4})", text)
        year = int(match.group(1)) if match else None

        link = await item.query_selector(self.LINK_SELECTOR)
        if not link:
            return None

        href = await link.get_attribute("href")
        if not href:
            return None

        status = await self.extract_reading_status(item)
        activated = self._STATUS_TO_BOOL.get(status)  # None if unknown

        return BookInfo(
            url=BASE_URL + href,
            year=year,
            activated=activated,
        )

    async def collect_books_under_year(
        self, max_year: int, limit: int, max_pages: int = 5
    ) -> list[BookInfo]:
        collected: list[BookInfo] = []
        pages_checked = 0

        while len(collected) < limit and pages_checked < max_pages:
            pages_checked += 1

            results = await self.get_results()

            for item in results:
                if len(collected) >= limit:
                    break

                info = await self.extract_card_info(item)

                if info is None or info.year is None:
                    continue

                if info.year <= max_year:
                    collected.append(info)

            if len(collected) < limit and pages_checked < max_pages:
                moved = await self.go_to_next_page()
                if not moved:
                    break

        return collected

    async def search_books_by_title_under_year(
        self, query: str, max_year: int, limit: int = 5
    ) -> list[BookInfo]:
        await self.search(query)
        print(f"Searching for '{query}' and filtering by year <= {max_year}...")
        return await self.collect_books_under_year(
            max_year, limit, max_pages=5
        )
