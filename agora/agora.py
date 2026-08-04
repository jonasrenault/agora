import logging
from datetime import datetime
from pathlib import Path

from patchright.async_api import Page, async_playwright
from PIL import Image

LOGGER = logging.getLogger(__name__)

TIMEOUT_1S = 1000


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
    date: datetime,
):
    LOGGER.info(f"Attempting to book an activity for {date}.")
    await page.get_by_role("button", name="..//assets/img/reservations.").click(
        timeout=TIMEOUT_1S
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
    home_page: str = "https://portalssl.agoraplus.fr/images_stmalo/v3/pck_home/home_view_local.html#/",
    email: str = "khadiata.sow@gmail.com",
    pwd: str = "",
    headless: bool = False,
    save_dir: Path = Path.cwd() / "runs",
) -> None:
    """
    Book a slot on Agora Plus (synchronous version).
    """
    if not save_dir.exists():
        save_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        LOGGER.info(f"Visiting {home_page} .")
        await page.goto(home_page, wait_until="networkidle")
        try:
            await _login(page, email, pwd)
            await _book(page, datetime.now())
        except Exception as e:
            LOGGER.error(
                f"An exception occured while visiting {home_page}.", exc_info=True
            )
            await _log_page(page, save_dir)
            raise e
        await _log_page(page, save_dir)
