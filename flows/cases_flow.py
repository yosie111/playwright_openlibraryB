from config import (
    PERF_THRESHOLD_BOOK_MS,
    PERF_THRESHOLD_READING_LIST_MS,
    PERF_THRESHOLD_SEARCH_MS,
)
from pages import BookSearchPage, ReadingListPage
from pages.reading_list_page import books_needing_add
from performance import measure_page_performance


async def run_case(case, page, username, collector):
    """Run a single CSV-driven test case end-to-end with measurements."""
    print(
        f"\n--- Case: '{case.query}' "
        f"(year <= {case.max_year}, limit {case.limit}) ---"
    )

    # Search and measure results page.
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

    # Collect filtered books.
    books = await search_page.collect_books_under_year(
        case.max_year, case.limit, max_pages=5
    )
    print(f"Found {len(books)} books:")
    for b in books:
        print(f"  [{b.activated}] [{b.year}] {b.url}")

    to_add = books_needing_add(books)
    reading_list_page = ReadingListPage(page)

    # Measure first book page (if any).
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

    # Measure reading list page.
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

    # Add books and validate count.
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
