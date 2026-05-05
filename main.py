import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from config import BASE_URL, SCREENSHOTS_DIR
from pages import BookSearchPage, LoginPage, ReadingListPage, SessionPage
from pages.reading_list_page import books_needing_add

# Load .env from the script's directory (works regardless of cwd).
load_dotenv(Path(__file__).parent / ".env")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
PROFILE_DIR = "playwright_profile"


async def wait_for_y():
    while True:
        answer = await asyncio.to_thread(
            input,
            "Type Y and press Enter to close the browser: ",
        )

        if answer.strip().upper() == "Y":
            break

        print("Browser stays open. Type Y to close.")

async def show_want_to_read_list(reading_list_page, username):
    count = await reading_list_page.get_want_to_read_count(username)
    print(f"\n{username}'s want-to-read list has {count} books:")
    return count



async def main():
    async with async_playwright() as p:
        # launch_persistent_context returns a Context directly (not a
        # Browser). The browser is created and torn down implicitly.
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
        )

        try:
            # Persistent context opens with one blank page already.
            page = (
                context.pages[0] if context.pages else await context.new_page()
            )
            await page.goto(BASE_URL)

            

            # --- Login (only needed before adding to the reading list) -----
            session_page = SessionPage(page)
            username = await session_page.is_logged_in()
            if username!="not connected":
                email = os.environ.get("OPENLIBRARY_EMAIL")
                password = os.environ.get("OPENLIBRARY_PASSWORD")
                login_page = LoginPage(page)
                await login_page.goto()
                username = await login_page.login(email, password)
                if username:
                    print(f"Successfully logged in as {username}")
                else:
                    print("Login failed: check credentials and try again.")
                    return
                
            username=await session_page.get_username()
            print('str2',username)     
            
            # --- Search  ---------------------------------
            search_page = BookSearchPage(page)
            books = await search_page.search_books_by_title_under_year("Anthology", 1500, 2)
            print(f"Found {len(books)} books:")
            for b in books:
                #icon = {True: "+", False: " ", None: "?"}[b.activated]                
                print(f"  [{b.activated}] [{b.year}] {b.url}")
    
            # --- Add to reading list ---------------------------------------
            
            to_add = books_needing_add(books)            
            reading_list_page = ReadingListPage(page)
            await wait_for_y()

            #print(f"Adding {len(books)} books to the reading list...")
            number_of_books_before = await show_want_to_read_list(reading_list_page, username)

            await reading_list_page.add_books_to_reading_list(to_add )
            await reading_list_page.assert_reading_list_count(
                    username, number_of_books_before + len(to_add))
            print("Assertion passed: reading list count is correct after adding books.")
        finally:
            # The browser stays open until the user types Y.
            print("\nDone. Inspect the browser.")
            await wait_for_y()

            await context.close()
            print("Context closed.")


if __name__ == "__main__":
    asyncio.run(main())
