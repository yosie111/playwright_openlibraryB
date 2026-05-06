import os

from pages import LoginPage, SessionPage


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
