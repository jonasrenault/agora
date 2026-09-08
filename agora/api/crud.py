import logging
from datetime import datetime

from aredis_om import (
    NotFoundError,
    SchemaDetector,
    get_redis_connection,
)

from agora.api.models import User, UserCreate, UserUpdate
from agora.api.security import get_password_hash, verify_password
from agora.config import settings
from agora.crypto import encrypt

LOGGER = logging.getLogger(__name__)


async def create_user(*, user_create: UserCreate, is_superuser: bool = False) -> User:
    existing_user = await get_user_by_email(email=user_create.email)
    if existing_user:
        raise ValueError(f"User with email {user_create.email} already exists.")

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


async def update_user(*, db_user: User, user_in: UserUpdate) -> User:
    if user_in.email is not None:
        existing_user = await get_user_by_email(email=user_in.email)
        if existing_user:
            raise ValueError(f"User with email {user_in.email} already exists.")

    user_data = user_in.model_dump(exclude_unset=True)
    try:
        if user_data["password"]:
            user_data["hashed_password"] = get_password_hash(user_data["password"])
            del user_data["password"]
    except KeyError:
        pass

    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    await db_user.update(**user_data)
    return db_user


async def get_user_by_email(*, email: str) -> User | None:
    try:
        user: User | None = await User.find(User.email == email).first()  # type: ignore
        return user
    except NotFoundError:
        return None


async def init_db() -> None:
    if settings.REDIS_RESET_ON_STARTUP:
        LOGGER.warning("[yellow]⚠[/yellow] Resetting Redis database on startup.")
        client = get_redis_connection(url=settings.REDIS_URL)
        await client.flushdb()

    # Run migrations
    await SchemaDetector(conn=get_redis_connection(url=settings.REDIS_URL)).run()

    user = await get_user_by_email(email=settings.ADMIN_EMAIL)
    if not user:
        user_in = UserCreate(
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
        )
        user = await create_user(user_create=user_in, is_superuser=True)
        user.agora_email = settings.ADMIN_AGORA_EMAIL
        user.agora_password = encrypt(settings.ADMIN_AGORA_PASSWORD, settings.SECRET_KEY)
        await user.save()


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
