from datetime import date, datetime
from enum import Enum
from typing import Annotated, TypeVar

from aredis_om import EmbeddedJsonModel, Field, JsonModel, get_redis_connection
from pydantic import BaseModel, BeforeValidator, EmailStr

from agora.config import settings


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(BaseModel):
    sub: str | None = None


class EncryptedValue(BaseModel):
    salt: str
    nonce: str
    tag: str
    ciphertext: str


class User(JsonModel, index=True):  # type: ignore
    email: EmailStr = Field(index=True)
    username: str | None = Field(default=None, index=True)
    is_active: bool = Field(default=True, index=True)
    is_superuser: bool = Field(default=False, index=True)
    hashed_password: str = Field(index=False)
    created_at: datetime = Field(default_factory=datetime.now, index=True, sortable=True)

    # Google Credentials
    token: str | None = Field(default=None, index=False)
    refresh_token: str | None = Field(default=None, index=False)
    granted_scopes: list[str] | None = Field(default=None, index=False)

    # Agora
    agora_email: EmailStr | None = Field(default=None, index=False)
    agora_password: EncryptedValue | None = Field(default=None, index=False)
    agora_slots: list[date] | None = Field(default=None, index=False)

    class Meta:
        global_key_prefix = settings.REDIS_PREFIX
        model_key_prefix = "user"
        database = get_redis_connection(url=settings.REDIS_URL)


# ============================================================
# REQUEST/RESPONSE MODELS (avoid ExpressionProxy in schema)
# ============================================================


class UserCreate(BaseModel):
    email: EmailStr
    username: str | None = None
    password: str


# Properties to receive via API on update, all are optional
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    username: str | None = None
    password: str | None = None


def parse_date_list(value: str | list[str] | list[date] | None) -> list[date] | None:
    if isinstance(value, str):
        return [datetime.strptime(v, "%d/%m/%Y") for v in value.split(",")]
    if isinstance(value, list):
        result = []
        for v in value:
            if isinstance(v, str) and v:
                result.extend(
                    [
                        datetime.strptime(s.strip(), "%d/%m/%Y").date()
                        for s in v.split(",")
                    ]
                )
            elif isinstance(v, date):
                result.append(v)
        if not result:
            return None
        return result
    return value


# Validator to convert empty strings to None
T = TypeVar("T")
EmptyToNone = Annotated[T, BeforeValidator(lambda v: None if v == "" else v)]


class UserAgoraUpdate(BaseModel):
    agora_email: EmptyToNone[EmailStr | None] = None
    agora_password: EmptyToNone[str | None] = None
    agora_slots: Annotated[list[date] | None, BeforeValidator(parse_date_list)] = None


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


class AgoraResult(str, Enum):
    success = "success"  # slot was successfully reserved
    alert = "alert"  # slot was full, an alert was created instead
    already_booked = "already_booked"  # slot was already booked
    unavailable = "unavailable"  # slot was unavailable and an alert already existed
    not_found = "not_found"  # slot not found (e.g. weekend date)
    too_late = "too_late"  # too late to reserve slot


class AgoraSlot(BaseModel):
    slot: date
    result: AgoraResult | None = None


class AgoraRun(EmbeddedJsonModel, index=True):  # type: ignore

    started_at: datetime = Field(default_factory=datetime.now, index=True, sortable=True)
    finished_at: datetime = Field(default_factory=datetime.now, index=True, sortable=True)
    slots: list[AgoraSlot] = Field(default_factory=list, index=False)
