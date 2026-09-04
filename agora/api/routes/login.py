from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm

from agora.api import security
from agora.api.crud import authenticate_user
from agora.api.deps import CurrentUser
from agora.api.models import Token, UserResponse
from agora.config.settings import settings

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
async def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = Token(
        access_token=security.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
    )
    response.set_cookie(
        key="access_token",
        value=f"{token.token_type.capitalize()} {token.access_token}",
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
    )
    return token


@router.post("/login/test-token", response_model=UserResponse)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user
