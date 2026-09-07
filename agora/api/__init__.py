from pathlib import Path

from fastapi.templating import Jinja2Templates

ROOT_DIR = Path(__file__).parent.parent.parent

templates = Jinja2Templates(directory=ROOT_DIR / "templates")
