from typing import Any

from pwdlib import PasswordHash

from agora.api.models import UserInDB
from agora.config.settings import settings

type DB = dict[str, dict[str, Any]]

users_db = {
    "jonas@agora.fr": {
        "email": "jonas@agora.fr",
        "full_name": "Jonas Renault",
        "hashed_password": PasswordHash.recommended().hash(settings.ADMIN_PASSWORD),
        "is_active": True,
        "is_superuser": True,
    }
}


def get_db() -> DB:
    return users_db


def get_user(db: DB, email: str) -> UserInDB | None:
    if email in db:
        user_dict = db[email]
        return UserInDB(**user_dict)
    return None
