import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from config import BASE_URL, SCREENSHOTS_DIR
from pages import BookSearchPage, LoginPage, ReadingListPage, SessionPage
from pages.reading_list_page import books_needing_add
from utils import load_search_cases

# Load .env from the script's directory (works regardless of cwd).
load_dotenv(Path(__file__).parent / ".env")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
PROFILE_DIR = "playwright_profile"
CASES_CSV = Path(__file__).parent / "test_data" / "search_cases.csv"


async def wait_for_y():
    while True:
        answer = await asyncio.to_thread(
            input,
            "Type Y and press Enter to close the browser: ",
        )
        if answer.strip().upper() == "Y":
            break
        print("Browser stays open. Type Y to close.")


async def run_case(case, page, username):
    print(
        f"\n--- Case: '{case.query}' "
        f"(year <= {case.max_year}, limit {case.limit}) ---"
    )

    search_page = BookSearchPage(page)
    books = await search_page.search_books_by_title_under_year(
        case.query, case.max_year, case.limit
    )
    print(f"Found {len(books)} books:")
    for b in books:
        print(f"  [{b.activated}] [{b.year}] {b.url}")

    to_add = books_needing_add(books)
    reading_list_page = ReadingListPage(page)

    count_before = await reading_list_page.get_want_to_read_count(username)
    print(f"  Reading list before: {count_before}")

    await reading_list_page.add_books_to_reading_list(to_add)
    expected = count_before + len(to_add)
    await reading_list_page.assert_reading_list_count(username, expected)
    print(f"  PASS: reading list now has {expected} books")


async def main():
    cases = load_search_cases(CASES_CSV)
    print(f"Loaded {len(cases)} test cases from {CASES_CSV.name}")

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

            # --- Login (only needed before adding to the reading list) -----
            session_page = SessionPage(page)
            username = await session_page.is_logged_in()
            if not username:
                email = os.environ.get("OPENLIBRARY_EMAIL")
                password = os.environ.get("OPENLIBRARY_PASSWORD")
                login_page = LoginPage(page)
                await login_page.goto()
                await login_page.login(email, password)
                username = await session_page.is_logged_in()
                if username:
                    print(f"Successfully logged in as {username}")
                else:
                    print("Login failed: check credentials and try again.")
                    return

            # --- Run all CSV-driven cases ---------------------------------
            passed = failed = 0
            for case in cases:
                try:
                    await run_case(case, page, username)
                    passed += 1
                except AssertionError as exc:
                    failed += 1
                    print(f"  FAIL: {exc}")
                except Exception as exc:
                    failed += 1
                    print(f"  ERROR: {exc!r}")

            print(
                f"\nSummary: {passed} passed, {failed} failed, "
                f"{len(cases)} total"
            )

        finally:
            print("\nDone. Inspect the browser.")
            await wait_for_y()
            await context.close()
            print("Context closed.")


if __name__ == "__main__":
    asyncio.run(main())