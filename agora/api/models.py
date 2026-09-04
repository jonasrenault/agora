from datetime import date, datetime

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


class User(JsonModel, index=True):  # type: ignore
    email: EmailStr = Field(index=True)
    username: str | None = Field(default=None, index=True)
    is_active: bool = Field(default=True, index=True)
    is_superuser: bool = Field(default=False, index=True)
    hashed_password: str = Field(index=False)
    created_at: datetime = Field(default_factory=datetime.now, index=True, sortable=True)

    token: str | None = Field(default=None, index=False)
    refresh_token: str | None = Field(default=None, index=False)
    granted_scopes: list[str] | None = Field(default=None, index=False)

    class Meta:
        global_key_prefix = settings.REDIS_PREFIX
        model_key_prefix = "user"
        database = get_redis_connection(url=settings.REDIS_URL)


# ============================================================
# REQUEST/RESPONSE MODELS (avoid ExpressionProxy in schema)
# ============================================================


class UserCreate(BaseModel):
    email: str
    username: str | None = None
    password: str


# Properties to receive via API on update, all are optional
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    username: str | None = None
    password: str | None = None


class UserResponse(BaseModel):
    pk: str
    username: str | None = None
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UsersResponse(BaseModel):
    data: list[UserResponse]
    count: int
    page: int


class Slot(BaseModel):
    date: date
    color: SlotColor | None = None
