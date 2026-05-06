import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from config import BASE_URL, SCREENSHOTS_DIR
from flows.auth_flow import login_if_needed
from pages.book_search_page import BookSearchPage

# Load .env from the script's directory (works regardless of cwd).
load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
PROFILE_DIR = "playwright_profile"

# One-book run configuration
QUERY = "harry"
MAX_YEAR = 1950
LIMIT = 3


async def wait_for_y():
    while True:
        answer = await asyncio.to_thread(
            input,
            "Type Y and press Enter to close the browser: ",
        )
        if answer.strip().upper() == "Y":
            break
        print("Browser stays open. Type Y to close.")


async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
        )

        try:
            page = (
                context.pages[0] if context.pages else await context.new_page()
            )
            await page.goto(BASE_URL)

            username = await login_if_needed(page)
            if not username:
                print("Login was not completed. Stopping run.")
                return

            search_page = BookSearchPage(page)

            # `debug` parameter was removed from BookSearchPage.
            books = await search_page.search_books_by_title_under_year(
                query=QUERY,
                max_year=MAX_YEAR,
                limit=LIMIT,
            )

            print("\n=== One book result ===")
            if not books:
                print("No matching book was found.")
                return

            book = books[0]
            print(f"URL: {book.url}")
            print(f"Year: {book.year}")
            print(f"Activated: {book.activated}")

            await page.screenshot(
                path=str(Path(SCREENSHOTS_DIR) / "one_book_debug.png"),
                full_page=True,
            )
            print("Screenshot saved: one_book_debug.png")

        finally:
            print("\nDone. Inspect the browser.")
            await wait_for_y()
            await context.close()
            print("Context closed.")


if __name__ == "__main__":
    asyncio.run(main())
