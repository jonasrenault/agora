from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from agora.api import security
from agora.api.deps import CurrentUser, DBDep
from agora.api.models import Token, User
from agora.api.security import authenticate_user
from agora.config.settings import settings

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login_access_token(
    db: DBDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token", response_model=User)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user
