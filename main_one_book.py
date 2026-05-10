import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from config import BASE_URL, SCREENSHOTS_DIR
from flows.auth_flow import load_saved_session, login_if_needed
from pages.book_search_page import BookSearchPage


# Load .env
load_dotenv(Path(__file__).parent / ".env")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
PROFILE_DIR = "playwright_profile"

# One-book run configuration
QUERY = "History"
MAX_YEAR = 1900
LIMIT = 30


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
            await load_saved_session(context)

            page = (
                context.pages[0] if context.pages else await context.new_page()
            )
            await page.goto(BASE_URL, wait_until="domcontentloaded")

            username = await login_if_needed(page)
            if not username:
                print("Login was not completed. Stopping run.")
                return

            search_page = BookSearchPage(page)

            urls = await search_page.search_books_by_title_under_year(
                query=QUERY,
                max_year=MAX_YEAR,
                limit=LIMIT,
            )

            print(f"\n=== Found {len(urls)} books ===")

            if not urls:
                print("No matching book was found.")
                return

            for i, url in enumerate(urls, start=1):
                print(f"\nBook #{i}")
                print(f"URL: {url}")

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
