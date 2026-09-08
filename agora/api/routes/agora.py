from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from agora.agora import book_agora
from agora.api import templates
from agora.api.deps import CurrentUser
from agora.api.render import create_context

router = APIRouter(prefix="/agora", tags=["agora"])


@router.post("/agora")
async def book_slot(*, current_user: CurrentUser):
    """
    Book a slot on agora.
    """
    if not current_user.agora_slots:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="No slots to reserve for current user.",
        )

    await book_agora(dates=current_user.agora_slots)


@router.get("/agora")
async def agora_settings_page(
    request: Request, current_user: CurrentUser
) -> HTMLResponse:
    """
    Page to update user's agora settings.
    """
    return templates.TemplateResponse(
        request=request, name="user_agora.html", context=create_context(current_user)
    )
