from typing import Any

from agora.api.models import User
from agora.config import settings


def create_context(current_user: User | None):
    context: dict[str, Any] = {"agora_url": settings.AGORA_HOME_PAGE}
    if current_user:
        context["user"] = {
            "username": current_user.username,
            "email": current_user.email,
            "is_linked": current_user.granted_scopes is not None,
        }
    return context
