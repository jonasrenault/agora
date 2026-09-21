import base64
from collections.abc import Iterable
from datetime import date, datetime, timezone
from enum import Enum
from typing import Annotated, TypeVar

from aredis_om import EmbeddedJsonModel, Field, JsonModel, get_redis_connection
from pydantic import BaseModel, BeforeValidator, EmailStr, computed_field
from pydantic import Field as PydanticField

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


class SlotAutomationResult(str, Enum):
    success = "success"  # slot was successfully reserved
    alert = "alert"  # slot was full, an alert was created instead
    already_booked = "already_booked"  # slot was already booked
    unavailable = "unavailable"  # slot was unavailable and an alert already existed
    not_found = "not_found"  # slot not found (e.g. weekend date)
    too_late = "too_late"  # too late to reserve slot


class AgoraSlot(BaseModel):
    slot: date
    result: SlotAutomationResult | None = None

    @computed_field  # type: ignore[misc]
    @property
    def result_class(self) -> str:
        if self.result is SlotAutomationResult.success:
            return "success"
        if self.result is SlotAutomationResult.alert:
            return "info"
        if self.result is SlotAutomationResult.already_booked:
            return "secondary"
        if self.result is SlotAutomationResult.unavailable:
            return "error"
        return "warning"

    @computed_field  # type: ignore[misc]
    @property
    def result_tooltip(self) -> str:
        if self.result is SlotAutomationResult.success:
            return "Booked successfully"
        if self.result is SlotAutomationResult.alert:
            return "Alert created"
        if self.result is SlotAutomationResult.already_booked:
            return "Slot was already booked"
        if self.result is SlotAutomationResult.unavailable:
            return "Slot was full"
        return "Unable to book slot"


class AutomationRun(EmbeddedJsonModel):
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    slots: list[AgoraSlot] = Field(default_factory=list)

    error: bool = Field(default=False)
    logs: str = Field(default="")
    screenshot: str | None = Field(default=None)


class User(JsonModel, index=True):  # type: ignore
    email: EmailStr = Field(index=True)
    username: str | None = Field(default=None, index=True)
    is_active: bool = Field(default=True, index=True)
    is_superuser: bool = Field(default=False, index=True)
    hashed_password: str | None = Field(default=None, index=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True, sortable=True
    )

    # Google Credentials
    token: str | None = Field(default=None, index=False)
    refresh_token: str | None = Field(default=None, index=False)
    granted_scopes: list[str] | None = Field(default=None, index=False)
    google_api_history_id: str | None = Field(default=None, index=False)

    # Agora
    agora_email: EmailStr | None = Field(default=None, index=False)
    agora_password: EncryptedValue | None = Field(default=None, index=False)
    agora_slots: list[date] | None = Field(default=None, index=False)
    automation_runs: list[AutomationRun] = Field(default_factory=list, index=False)

    def remove_slots(self, dates: Iterable[date]):
        if self.agora_slots is not None:
            for d in dates:
                try:
                    self.agora_slots.remove(d)
                except ValueError:
                    continue
            if len(self.agora_slots) == 0:
                self.agora_slots = None

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
    password: str | None = None
    google_api_history_id: str | None = None
    token: str | None = None
    refresh_token: str | None = None
    granted_scopes: list[str] | None = None


def parse_date_list(value: str | list[str] | list[date] | None) -> list[date] | None:
    if isinstance(value, str):
        return [datetime.strptime(v.strip(), "%d/%m/%Y").date() for v in value.split(",")]
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


class AgoraCreate(BaseModel):
    headless: bool = False
    dry_run: bool = False


class GmailMessage(BaseModel):
    sender: str
    subject: str
    snippet: str


class GooglePubSubData(BaseModel):
    email: EmailStr = PydanticField(alias="emailAddress")
    history_id: str = PydanticField(alias="historyId")


def parse_google_data(data: str) -> GooglePubSubData:
    return GooglePubSubData.model_validate_json(base64.b64decode(data).decode("utf-8"))


class GooglePubSubMessage(BaseModel):
    data: Annotated[GooglePubSubData, BeforeValidator(parse_google_data)]
    messageId: str
    publishTime: datetime


class GooglePubSubPayload(BaseModel):
    message: GooglePubSubMessage
    subscription: str
