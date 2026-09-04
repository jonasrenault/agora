from datetime import datetime

from aredis_om import NotFoundError

from agora.api.models import User, UserCreate
from agora.api.security import get_password_hash, verify_password
from agora.config.settings import settings


async def create_user(*, user_create: UserCreate, is_superuser: bool = False) -> User:
    db_obj = User.model_validate(
        {
            **user_create.model_dump(),
            "hashed_password": get_password_hash(user_create.password),
            "created_at": datetime.now(),
            "is_superuser": is_superuser,
        }
    )

    await db_obj.save()
    return db_obj


async def get_user_by_email(*, email: str) -> User | None:
    try:
        user: User | None = await User.find(User.email == email).first()  # type: ignore
        return user
    except NotFoundError:
        return None


async def init_db() -> None:
    user = await get_user_by_email(email=settings.ADMIN_EMAIL)
    if not user:
        user_in = UserCreate(
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
        )
        user = await create_user(user_create=user_in, is_superuser=True)


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"  # noqa: E501


async def authenticate_user(username: str, password: str) -> User | None:
    db_user = await get_user_by_email(email=username)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't
        # exist. This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user
