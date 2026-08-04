import locale
import logging
from datetime import date, datetime
from pathlib import Path

from PIL import Image
from playwright.async_api import Page, async_playwright

from agora.config.settings import settings

LOGGER = logging.getLogger(__name__)

TIMEOUT_1S = 1000
TIMEOUT_3S = 3000
TIMEOUT_5S = 5000


async def _log_page(page: Page, save_dir: Path, show: bool = False):
    """
    Log the current page by saving a screenshot and the page source to disk.

    Args:
        page (Page): the current page.
        save_dir (Path, optional): the directory to save the screenshot and page
            source to.
        show (bool, optional): show the screenshot. Defaults to False.
    """
    LOGGER.info(f"Saving screenshot and page contents to [bold blue]{save_dir}[/].")
    screen = save_dir / "screenshot.png"
    await page.screenshot(path=screen)
    html = await page.content()
    with open(save_dir / "page.html", "w") as f:
        f.write(html)
    if show:
        screenshot = Image.open(screen)
        screenshot.show()


async def _book(
    page: Page,
    date: date,
):
    if date < datetime.now().date():
        raise ValueError(f"Unable to book a slot in the past ({date})")

    LOGGER.info(f"Attempting to book an activity for {date}.")
    await page.get_by_role("button", name="..//assets/img/reservations.").wait_for(
        state="visible"
    )
    await page.screenshot(path=Path.cwd() / "runs" / "before_booking.png")
    await page.get_by_role("button", name="..//assets/img/reservations.").click(
        timeout=TIMEOUT_5S
    )

    target_month = date.strftime("%B")  # e.g., "août"
    LOGGER.info(f"Selecting target month {target_month}.")
    await page.locator("#date-selector").click(timeout=TIMEOUT_5S)
    while not (
        await page.locator(".mdp-calendar-monthyear").text_content(timeout=TIMEOUT_1S)
        == target_month
    ):
        await page.get_by_role("button", name="next month").click(timeout=TIMEOUT_1S)

    LOGGER.info(f"Selecting target day {date.day}.")
    await page.get_by_role("button", name=str(date.day), exact=True).click(
        timeout=TIMEOUT_5S
    )


async def _login(page: Page, email: str, pwd: str):
    LOGGER.info(f"Attempting to log in with email: {email}.")
    await page.get_by_role("button", name="Display login dialog").click(
        timeout=TIMEOUT_1S
    )
    await page.get_by_role("textbox", name="Courriel").fill(email, timeout=TIMEOUT_1S)
    await page.get_by_role("textbox", name="Mot de passe").fill(pwd, timeout=TIMEOUT_1S)
    await page.get_by_role("button", name="Login", exact=True).click(timeout=TIMEOUT_1S)
    LOGGER.info("Login completed.")


async def book_agora(
    home_page: str = settings.AGORA_HOME_PAGE,
    email: str = settings.AGORA_EMAIL,
    pwd: str = settings.AGORA_PASSWORD,
    date: date = date(2026, 10, 21),
    headless: bool = False,
    save_dir: Path = Path.cwd() / "runs",
    locale_code: str = "fr_FR",
) -> None:
    """
    Book a slot on Agora Plus (synchronous version).
    """
    if not save_dir.exists():
        save_dir.mkdir(parents=True, exist_ok=True)

    # Set the locale for date formatting
    locale.setlocale(locale.LC_ALL, locale_code)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        LOGGER.info(f"Visiting {home_page} .")
        await page.goto(home_page, wait_until="networkidle")
        try:
            await _login(page, email, pwd)
            await _book(page, date)
        except Exception as e:
            LOGGER.error(
                f"An exception occured while visiting {home_page}.", exc_info=True
            )
            await _log_page(page, save_dir)
            raise e
        await _log_page(page, save_dir)
