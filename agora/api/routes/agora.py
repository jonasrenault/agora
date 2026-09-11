import asyncio
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from agora.agora import book_agora
from agora.api import templates
from agora.api.deps import CurrentUser
from agora.api.models import AgoraResult, UserAgoraUpdate
from agora.api.render import create_context
from agora.config import settings
from agora.crypto import encrypt

router = APIRouter(prefix="/agora", tags=["agora"])


@router.post("/book")
async def book(*, request: Request, current_user: CurrentUser):
    """
    Book user's slots on Agora.
    """
    if not current_user.agora_slots:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="No slots to reserve for current user.",
        )

    semaphore = asyncio.Semaphore(1)  # Max 1 concurrent tasks
    async with semaphore:
        run = await book_agora(dates=current_user.agora_slots, headless=False)
        current_user.agora_runs.append(run)
        current_user.remove_slots(
            [s.slot for s in run.slots if s.result is AgoraResult.success]
        )
        await current_user.save()

    return RedirectResponse(
        url=request.url_for("runs"), status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/runs")
async def runs(request: Request, current_user: CurrentUser) -> HTMLResponse:
    """
    Page to list Agora Runs
    """
    context = create_context(current_user)
    context["runs"] = current_user.agora_runs
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
    Book a slot on agora.
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
