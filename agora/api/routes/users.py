from aredis_om import NotFoundError
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from agora.api import crud, templates
from agora.api.deps import CurrentUser, get_current_active_superuser
from agora.api.models import User, UserCreate, UserResponse, UsersResponse
from agora.api.render import create_context

router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(get_current_active_superuser)]
)


@router.get("/list")
async def users_list_page(
    request: Request,
    current_user: CurrentUser,
    username: str | None = None,
    email: str | None = None,
    is_active: bool | None = None,
    sort_by: str = Query("created_at", pattern="^-?created_at$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> HTMLResponse:
    """
    Page to list users.
    """
    users = await list_users(
        username=username,
        email=email,
        is_active=is_active,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    context = create_context(current_user)
    context["users"] = users
    return templates.TemplateResponse(
        request=request, name="pages/users.html", context=context
    )


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, is_superuser: bool = False):
    """Create a new user"""
    db_user = await crud.create_user(user_create=user, is_superuser=is_superuser)
    return db_user


@router.get("/{pk}", response_model=UserResponse)
async def get_user(pk: str):
    """Get user by primary key"""
    try:
        user = await User.get(pk)
        return user
    except NotFoundError:
        raise HTTPException(404, f"User with pk {pk} not found.")


@router.get("/", response_model=UsersResponse)
async def list_users(
    username: str | None = None,
    email: str | None = None,
    is_active: bool | None = None,
    sort_by: str = Query("created_at", pattern="^-?created_at$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """
    Query users with filters, sorting, pagination.
    """
    filters = []
    if username:
        filters.append(User.username == username)
    if email:
        filters.append(User.email == email)
    if is_active is not None:
        filters.append(User.is_active == is_active)

    query = User.find(*filters) if filters else User.find()

    # Sorting
    query = query.sort_by(sort_by)

    # Pagination
    offset = (page - 1) * page_size
    results = await query.copy(offset=offset, limit=page_size).all()

    # Count
    count = await query.count()

    users_public = [UserResponse.model_validate(user.model_dump()) for user in results]  # type: ignore
    return UsersResponse(data=users_public, count=count, page=page)  # type: ignore


@router.delete("/{pk}")
async def delete_user(pk: str):
    """Delete user by pk"""
    try:
        await User.get(pk)  # Verify exists
        await User.delete(pk)
        return {"deleted": pk}
    except NotFoundError:
        raise HTTPException(404, "User not found")
