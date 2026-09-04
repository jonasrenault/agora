from datetime import date, datetime
from typing import Annotated

from aredis_om import Field, JsonModel, get_redis_connection
from pydantic import BaseModel, EmailStr

from agora.agora import SlotColor
from agora.config.settings import settings


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(BaseModel):
    sub: str | None = None


class User(JsonModel):
    email: EmailStr = Field(index=True)
    username: Annotated[str | None, Field(index=True)] = None
    is_active: Annotated[bool, Field(index=True)] = True
    is_superuser: Annotated[bool, Field(index=True)] = False
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now, index=True, sortable=True)

    class Meta:
        global_key_prefix = settings.REDIS_PREFIX
        model_key_prefix = "user"
        database = get_redis_connection(url=settings.REDIS_OM_URL)


# ============================================================
# REQUEST/RESPONSE MODELS (avoid ExpressionProxy in schema)
# ============================================================


class UserCreate(BaseModel):
    email: str
    username: str | None = None
    password: str


class UserResponse(BaseModel):
    pk: str
    username: str | None = None
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime


class Slot(BaseModel):
    date: date
    color: SlotColor | None = None
