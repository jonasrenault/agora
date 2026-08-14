import locale
import logging
from datetime import date, datetime
from enum import Enum
from pathlib import Path

from patchright.async_api import Browser, BrowserContext, Page, async_playwright
from patchright.async_api import TimeoutError as PlaywrightTimeoutError
from PIL import Image

from agora.config.settings import settings

LOGGER = logging.getLogger(__name__)

TIMEOUT_1S = 1000
TIMEOUT_2S = 2000
TIMEOUT_3S = 3000
TIMEOUT_5S = 5000

STORAGE_STATE_FILE = "storage_state.json"
SESSION_STORAGE_FILE = "session.json"


class SlotColor(str, Enum):
    red = "red"
    green = "green"
    yellow = "yellow"


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


async def _reserve_slot(page: Page, date: date) -> SlotColor:
    # Count header dates and find the index of the target date
    target_date = date.strftime("%Y-%m-%d")
    headers = await page.locator("th.fc-day-header").all()
    header_dates = [await header.get_attribute("data-date") for header in headers]
    LOGGER.info(f"Found {len(header_dates)} header dates: {header_dates}")
    slot_index = header_dates.index(target_date)
    LOGGER.info(f"Target date index: {slot_index}")

    # Find the target slot and check its color
    slots = await page.locator("a.fc-event").all()
    slot = slots[slot_index]
    bg_color = await slot.evaluate("el => window.getComputedStyle(el).backgroundColor")
    slot_color = _get_slot_color(bg_color)
    LOGGER.info(
        f"Found {len(slots)} slots, target slot is {slot_color.value} ({bg_color})"
    )

    # Click the slot and check for alert popups
    await slot.click(timeout=TIMEOUT_5S)

    try:
        # An alert already exists.
        await page.get_by_text("Une alerte a déjà été créée").wait_for(
            state="visible", timeout=TIMEOUT_2S
        )
        LOGGER.warning("Target slot is red and an alert has already been created.")
        return slot_color
    except (PlaywrightTimeoutError, TimeoutError):
        pass

    try:
        # Create a new alert.
        await page.get_by_text("Créer une alerte", exact=True).click(timeout=TIMEOUT_2S)
        LOGGER.warning("Target slot is red. A new alert has been created.")
        return slot_color
    except (PlaywrightTimeoutError, TimeoutError):
        pass

    # Click on submit button
    LOGGER.info("Submitting slot reservation.")
    await page.get_by_role("button", name="Submit").click(timeout=TIMEOUT_1S)

    try:
        await page.get_by_role("heading", name="Hmm... c'est embarrassant.").wait_for(
            state="visible", timeout=TIMEOUT_2S
        )
        LOGGER.warning("Something went wrong, no reservations were submitted.")
        return slot_color
    except (PlaywrightTimeoutError, TimeoutError):
        LOGGER.info("Reservation successful.")
        return slot_color


def _get_slot_color(bg_color: str) -> SlotColor:
    red, green, blue = [int(x) for x in bg_color[4:-1].split(",")]
    if red > 200 and green < 200 and blue < 200:
        return SlotColor.red
    elif red > 200 and green > 200 and blue < 200:
        return SlotColor.yellow

    return SlotColor.green


async def _select_date(
    page: Page,
    date: date,
):
    if date < datetime.now().date():
        raise ValueError(f"Unable to select a date in the past ({date})")

    LOGGER.info(f"Selecting date {date}")
    await page.locator("#date-selector").click(timeout=TIMEOUT_5S)

    target_month = date.strftime("%B")  # e.g., "août"
    LOGGER.info(f"Selecting target month {target_month}")
    while not (
        await page.locator(".mdp-calendar-monthyear").text_content(timeout=TIMEOUT_1S)
        == target_month
    ):
        await page.get_by_role("button", name="next month").click(timeout=TIMEOUT_1S)

    LOGGER.info(f"Selecting target day {date.day}")
    await page.locator(".mdp-calendar-days").get_by_text(str(date.day), exact=True).click(
        timeout=TIMEOUT_5S
    )

    LOGGER.info("Validating date selection")
    await page.get_by_role("button", name="OK").click(timeout=TIMEOUT_1S)

    await page.wait_for_timeout(TIMEOUT_2S)  # Wait for the calendar to update


async def _go_to_reservations(page: Page):
    LOGGER.info("Navigating to reservations page.")
    await page.get_by_role("button", name="..//assets/img/reservations.").click(
        timeout=TIMEOUT_5S
    )


async def _login(page: Page, email: str, pwd: str) -> bool:
    """
    Attempt to login from the Dashboard page.

    Args:
        page (Page): the current page.
        email (str): the login email.
        pwd (str): the login password.

    Returns:
        bool: True if login was successfull. False if already logged in.
    """
    try:
        await page.get_by_role("button", name="Display login dialog").wait_for(
            state="visible", timeout=TIMEOUT_5S
        )
    except TimeoutError:
        LOGGER.info("Login button not found. Skipping login")
        return False

    LOGGER.info(f"Attempting to log in with email: {email}")
    await page.get_by_role("button", name="Display login dialog").click(
        timeout=TIMEOUT_1S
    )
    await page.get_by_role("textbox", name="Courriel").fill(email, timeout=TIMEOUT_1S)
    await page.get_by_role("textbox", name="Mot de passe").fill(pwd, timeout=TIMEOUT_1S)
    await page.get_by_role("button", name="Login", exact=True).click(timeout=TIMEOUT_1S)
    LOGGER.info("Login completed")
    return True


async def _save_state(context: BrowserContext, page: Page, save_dir: Path):
    # Save the storage state to a JSON file
    storage_state_path = save_dir / STORAGE_STATE_FILE
    LOGGER.info(f"Saving storage state to {storage_state_path}")
    await context.storage_state(path=storage_state_path)

    session_storage_path = save_dir / SESSION_STORAGE_FILE
    LOGGER.info(f"Saving session storage to {session_storage_path}")
    session_storage = await page.evaluate("() => JSON.stringify(sessionStorage)")
    with open(session_storage_path, "w") as f:
        f.write(session_storage)


async def _get_context(browser: Browser, save_dir: Path) -> BrowserContext:
    """
    Get a browser context, loading the storage state if it exists.

    Args:
        browser (Browser): the browser instance.
        save_dir (Path): the directory to save the storage state to.

    Returns:
        BrowserContext: the browser context.
    """
    storage_state_path = save_dir / STORAGE_STATE_FILE
    if storage_state_path.exists():
        LOGGER.info(f"Loading storage state from {storage_state_path}")
        context = await browser.new_context(storage_state=storage_state_path)

        session_storage_path = save_dir / SESSION_STORAGE_FILE
        if session_storage_path.exists():
            LOGGER.info(f"Loading session storage from {session_storage_path}")
            with open(session_storage_path, "r") as f:
                session_storage = f.read()
            await context.add_init_script("""(storage => {
const entries = JSON.parse(storage)
for (const [key, value] of Object.entries(entries)) {
    window.sessionStorage.setItem(key, value)
}
})('""" + session_storage + "')")
    else:
        LOGGER.info(
            f"No storage state found at {storage_state_path}. Creating new context."
        )
        context = await browser.new_context()
    return context


async def book_agora(
    home_page: str = settings.AGORA_HOME_PAGE,
    email: str = settings.AGORA_EMAIL,
    pwd: str = settings.AGORA_PASSWORD,
    date: date = date(2026, 10, 22),
    headless: bool = False,
    save_dir: Path = Path.cwd() / "runs",
    locale_code: str = "fr_FR",
) -> SlotColor | None:
    if not save_dir.exists():
        save_dir.mkdir(parents=True, exist_ok=True)

    # Set the locale for date formatting
    locale.setlocale(locale.LC_ALL, locale_code)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await _get_context(browser, save_dir)
        page = await context.new_page()

        LOGGER.info(f"Visiting {home_page}")
        await page.goto(home_page, wait_until="networkidle")
        try:
            # Login if required and save state
            logged_in = await _login(page, email, pwd)
            if logged_in:
                await _save_state(context, page, save_dir)

            await _go_to_reservations(page)
            await _select_date(page, date)
            color = await _reserve_slot(page, date)
        except Exception as e:
            LOGGER.error(
                f"An exception occured while visiting {home_page}", exc_info=True
            )
            await _log_page(page, save_dir)
            raise e

        await _log_page(page, save_dir)
        return color
