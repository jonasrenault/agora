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
    AGORA_EMAIL: str = ""
    # User password for logging into Agora Plus
    AGORA_PASSWORD: str = ""


settings = Settings()
