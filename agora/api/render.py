from typing import Any

from agora.api.models import User
from agora.config import settings


def create_context(current_user: User | None):
    context: dict[str, Any] = {"agora_url": settings.AGORA_HOME_PAGE}
    if current_user:
        context["user"] = {
            "username": current_user.username,
            "email": current_user.email,
            "is_superuser": current_user.is_superuser,
            "last_watch": current_user.last_watch,
            "last_notification": current_user.last_notification,
            "last_run": (
                current_user.automation_runs[-1].started_at
                if current_user.automation_runs
                else None
            ),
        }
    return context
