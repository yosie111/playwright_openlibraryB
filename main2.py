import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from config import (
    BASE_URL,
    PERF_REPORT_PATH,
    PERF_THRESHOLD_BOOK_MS,
    PERF_THRESHOLD_READING_LIST_MS,
    PERF_THRESHOLD_SEARCH_MS,
    SCREENSHOTS_DIR,
)
from pages import BookSearchPage, LoginPage, ReadingListPage, SessionPage
from pages.reading_list_page import books_needing_add
from performance import PerformanceCollector, measure_page_performance
from utils import load_search_cases

# Load .env from the script's directory (works regardless of cwd).
load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

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


async def login_if_needed(page):
    """Ensure the user is logged in. Returns username or None on failure."""
    session_page = SessionPage(page)
    username = await session_page.is_logged_in()
    if username:
        return username

    login_page = LoginPage(page)
    await login_page.goto()
    await login_page.login(
        os.environ.get("OPENLIBRARY_EMAIL"),
        os.environ.get("OPENLIBRARY_PASSWORD"),
    )

    username = await session_page.is_logged_in()
    if username:
        print(f"Successfully logged in as {username}")
    else:
        print("Login failed: check credentials and try again.")
    return username


async def run_case(case, page, username, collector):
    """Run a single CSV-driven test case end-to-end with measurements."""
    print(
        f"\n--- Case: '{case.query}' "
        f"(year <= {case.max_year}, limit {case.limit}) ---"
    )

    # --- Search + measure search page ---------------------------------
    search_page = BookSearchPage(page)
    await search_page.search(case.query)

    collector.add(
        await measure_page_performance(
            page,
            url=page.url,
            threshold_ms=PERF_THRESHOLD_SEARCH_MS,
            label=f"search_page:{case.query}",
        )
    )

    # Collect filtered books from the same search results.
    books = await search_page.collect_books_under_year(
        case.max_year, case.limit, max_pages=5,
    )
    print(f"Found {len(books)} books:")
    for b in books:
        print(f"  [{b.activated}] [{b.year}] {b.url}")

    to_add = books_needing_add(books)
    reading_list_page = ReadingListPage(page)

    # --- Measure first book-page navigation (if any) ------------------
    if to_add:
        await reading_list_page.book_page.goto(to_add[0].url)
        collector.add(
            await measure_page_performance(
                page,
                url=to_add[0].url,
                threshold_ms=PERF_THRESHOLD_BOOK_MS,
                label="book_page",
            )
        )

    # --- Reading list count + measure reading list page ---------------
    count_before = await reading_list_page.get_want_to_read_count(username)
    collector.add(
        await measure_page_performance(
            page,
            url=page.url,
            threshold_ms=PERF_THRESHOLD_READING_LIST_MS,
            label="reading_list_page",
        )
    )

    print(f"  Reading list before: {count_before}")

    # --- Add and assert -----------------------------------------------
    await reading_list_page.add_books_to_reading_list(to_add)
    expected = count_before + len(to_add)
    await reading_list_page.assert_reading_list_count(username, expected)
    print(f"  PASS: reading list now has {expected} books")


async def run_all_cases(cases, page, username, collector):
    """Run every case; track pass/fail without aborting the run."""
    passed = failed = 0
    for case in cases:
        try:
            await run_case(case, page, username, collector)
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


async def main():
    cases = load_search_cases(CASES_CSV)
    print(f"Loaded {len(cases)} test cases from {CASES_CSV.name}")

    collector = PerformanceCollector()

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
                return

            await run_all_cases(cases, page, username, collector)

        finally:
            # Always write the report — even if the run crashed mid-way.
            collector.write_report(PERF_REPORT_PATH)

            print("\nDone. Inspect the browser.")
            await wait_for_y()
            await context.close()
            print("Context closed.")


if __name__ == "__main__":
    asyncio.run(main())