from pathlib import Path

from fastapi.templating import Jinja2Templates

from agora.api.models import AgoraResult

ROOT_DIR = Path(__file__).parent.parent.parent

templates = Jinja2Templates(directory=ROOT_DIR / "templates")


def result_to_class(value: AgoraResult, arg1: str = "") -> str:
    if value is AgoraResult.success:
        klass = "success"
    elif value is AgoraResult.alert:
        klass = "info"
    elif value is AgoraResult.already_booked:
        klass = "secondary"
    elif value is AgoraResult.unavailable:
        klass = "error"
    else:
        klass = "warning"
    return f"{arg1}{klass}"


def result_to_tooltip(value: AgoraResult) -> str:
    if value is AgoraResult.success:
        res = "Booked successfully"
    elif value is AgoraResult.alert:
        res = "Alert created"
    elif value is AgoraResult.already_booked:
        res = "Slot was already booked"
    elif value is AgoraResult.unavailable:
        res = "Slot was full"
    else:
        res = "Unable to book slot"
    return res


templates.env.filters["result_class"] = result_to_class
templates.env.filters["result_tooltip"] = result_to_tooltip
