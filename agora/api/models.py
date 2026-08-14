from datetime import date

from pydantic import BaseModel, EmailStr

from agora.agora import SlotColor


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(BaseModel):
    sub: str | None = None


class User(BaseModel):
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserInDB(User):
    hashed_password: str


class Slot(BaseModel):
    date: date
    color: SlotColor | None = None
