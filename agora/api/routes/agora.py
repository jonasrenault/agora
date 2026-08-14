from fastapi import APIRouter

from agora.agora import book_agora
from agora.api.deps import CurrentUser
from agora.api.models import Slot

router = APIRouter(prefix="/agora", tags=["agora"])


@router.post("/agora")
async def book_slot(*, current_user: CurrentUser, slot: Slot) -> Slot:
    """
    Book a slot on agora.
    """
    slot.color = await book_agora(date=slot.date)
    return slot
