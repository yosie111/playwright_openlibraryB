import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from config import (
    BASE_URL,
    PERF_REPORT_PATH,
    SCREENSHOTS_DIR,
)
from flows.auth_flow import load_saved_session, login_if_needed
from flows.cases_flow import run_all_cases
from performance import PerformanceCollector
from utils import load_search_cases

# Load .env
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
        
async def wait_for_enter():
    await asyncio.to_thread(input, "Press Enter to close the browser: ")

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
            # Restore cookies from storage_state.json (if a previous run saved them).
            # The persistent profile already keeps cookies between runs, but this
            # is a belt-and-braces fallback for when the profile dir is wiped.
            await load_saved_session(context)

            page = (
                context.pages[0] if context.pages else await context.new_page()
            )
            await page.goto(BASE_URL, wait_until="domcontentloaded")

            username = await login_if_needed(page)
            if not username:
                return

            await run_all_cases(cases, page, username, collector)

        finally:
            # Always write the report
            collector.write_report(PERF_REPORT_PATH)

            print("\nDone. Inspect the browser.")
            await wait_for_enter()
            await context.close()
            print("Context closed.")


if __name__ == "__main__":
    asyncio.run(main())
