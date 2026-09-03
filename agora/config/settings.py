from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    # Agora Plus home page URL
    AGORA_HOME_PAGE: str = (
        "https://portalssl.agoraplus.fr/images_stmalo/v3/pck_home/home_view_local.html#/"
    )
    # User email for logging into Agora Plus
    AGORA_EMAIL: str
    # User password for logging into Agora Plus
    AGORA_PASSWORD: str

    ################
    # FASTAPI SETTINGS
    ################
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    FASTAPI_ENV: Literal["development"] | None = None
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    PROJECT_NAME: str
    ADMIN_PASSWORD: str

    ################
    # GOOGLE API SETTINGS
    ################
    CREDENTIALS_DIR: Path = Path(__file__).parent.parent.parent / ".credentials"
    CREDENTIALS_FILE_NAME: str = "credentials.json"
    TOKEN_FILE_NAME: str = "token.json"


settings = Settings()  # type: ignore
