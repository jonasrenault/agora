from fastapi.templating import Jinja2Templates

from agora.api.cache_assets import build_asset_map, make_asset_url
from agora.config import settings

templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

_asset_map = build_asset_map(settings.STATIC_DIR)
templates.env.globals["asset"] = lambda path: make_asset_url(_asset_map, path)
