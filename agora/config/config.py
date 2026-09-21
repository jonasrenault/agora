from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    ################
    # AGORA PORTAL SETTINGS
    ################
    AGORA_HOME_PAGE: str = (
        "https://portalssl.agoraplus.fr/images_stmalo/v3/pck_home/home_view_local.html#/"
    )
    AGORA_NOTIFICATIONS_SENDER: str = "test"

    ################
    # REDIS SETTINGS
    ################
    REDIS_URL: str = "redis://default:****@obedient-crack-pie.redis.io:17853"
    REDIS_PREFIX: str = "agora"
    REDIS_RESET_ON_STARTUP: bool = False  # Reset the Redis database on startup

    ################
    # FASTAPI SETTINGS
    ################
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "changethis"
    FASTAPI_ENV: Literal["development"] | None = None
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    PROJECT_NAME: str = "Agora API"
    TEMPLATES_DIR: Path = ROOT_DIR / "templates"
    STATIC_DIR: Path = ROOT_DIR / "static"

    ################
    # DEFAULT ADMIN SETTINGS
    ################
    ADMIN_EMAIL: str = "admin@agora.fr"
    ADMIN_PASSWORD: str = "changethis"
    # User email for logging into Agora Plus
    ADMIN_AGORA_EMAIL: str = "admin@agora.fr"
    # User password for logging into Agora Plus
    ADMIN_AGORA_PASSWORD: str = "changethis"

    ################
    # GOOGLE OAUTH API SETTINGS
    # https://github.com/googleapis/google-api-python-client/blob/main/docs/client-secrets.md
    ################
    GOOGLE_OAUTH_CLIENT_ID: str = "asdfjasdljfasdkjf"
    GOOGLE_OAUTH_CLIENT_SECRET: str = "changethis"
    GOOGLE_OAUTH_PROJECT_ID: str = "agora-098723"

    ################
    # GOOGLE API SETTINGS
    ################
    GOOGLE_WEBHOOK_TOPIC: str = "projects/myproject/topics/mytopic"
    GOOGLE_WEBHOOK_SUBSCRIPTION: str = "projects/myproject/subscriptions/mysubscription"
