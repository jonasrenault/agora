from typing import Annotated

from fastapi import APIRouter, Form, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from agora.api import templates
from agora.api.deps import CurrentUser
from agora.api.models import AgoraCreate, UserAgoraUpdate
from agora.api.render import create_context
from agora.automation import run_automation_for_user
from agora.config import settings
from agora.crypto import encrypt

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/")
async def run_automation(
    agora_params: Annotated[AgoraCreate, Form()],
    request: Request,
    current_user: CurrentUser,
    hx_request: Annotated[str | None, Header()] = None,
):
    """
    Run automation to book user's slots on Agora.
    """
    try:
        await run_automation_for_user(
            current_user, agora_params.headless, agora_params.dry_run
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )

    if hx_request:
        context = create_context(current_user)
        context["runs"] = current_user.automation_runs
        return templates.TemplateResponse(
            request=request, name="components/_runs.html", context=context
        )

    return current_user


@router.get("/")
async def runs(
    request: Request,
    current_user: CurrentUser,
    hx_request: Annotated[str | None, Header()] = None,
) -> HTMLResponse:
    """
    Page to list Agora Runs
    """
    context = create_context(current_user)
    context["runs"] = current_user.automation_runs
    if hx_request:
        return templates.TemplateResponse(
            request=request, name="components/_runs.html", context=context
        )
    return templates.TemplateResponse(
        request=request, name="pages/agora_runs.html", context=context
    )


@router.get("/settings")
async def agora_settings_page(
    request: Request, current_user: CurrentUser
) -> HTMLResponse:
    """
    Page to update user's agora settings.
    """
    context = create_context(current_user)
    if current_user.agora_email is not None:
        context["user"]["agora_email"] = current_user.agora_email
    if current_user.agora_slots is not None:
        context["user"]["agora_slots"] = ", ".join(
            [v.strftime("%d/%m/%Y") for v in current_user.agora_slots]
        )
    return templates.TemplateResponse(
        request=request, name="pages/agora_settings.html", context=context
    )


@router.post("/settings")
async def update_agora_settings(
    userUpdate: Annotated[UserAgoraUpdate, Form()],
    request: Request,
    current_user: CurrentUser,
) -> RedirectResponse:
    """
    Update current user's agora settings (slots, email, password).
    """
    user_data = userUpdate.model_dump(exclude_unset=True, exclude_none=True)
    if "agora_password" in user_data:
        user_data["agora_password"] = encrypt(
            user_data["agora_password"], settings.SECRET_KEY
        )
    if user_data:
        await current_user.update(**user_data)

    return RedirectResponse(
        url=request.url_for("agora_settings_page"), status_code=status.HTTP_303_SEE_OTHER
    )
