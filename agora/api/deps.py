from typing import Annotated

import jwt
from aredis_om import NotFoundError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from jwt import InvalidTokenError
from pydantic import ValidationError

from agora.api import security
from agora.api.models import TokenPayload, User
from agora.config import settings


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):

    async def __call__(self, request: Request) -> str | None:
        # 1. Try Header first (for Swagger UI)
        authorization = request.headers.get("Authorization")
        if not authorization:
            authorization = request.cookies.get("access_token")

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise self.make_not_authenticated_error()
            else:
                return None
        return param


oauth2_scheme = OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token", auto_error=False
)
TokenDep = Annotated[str | None, Depends(oauth2_scheme)]


async def get_optional_user(token: TokenDep) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not token_data.sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    try:
        user = await User.get(token_data.sub)
    except NotFoundError:
        return None
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def get_current_user(optional_user: OptionalUser) -> User:
    if not optional_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not optional_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return optional_user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


CurrentSuperUser = Annotated[User, Depends(get_current_active_superuser)]
