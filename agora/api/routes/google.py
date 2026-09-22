from datetime import datetime, timedelta, timezone
from typing import Annotated, cast

import requests
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient import errors as google_api_errors

from agora.api import security, templates
from agora.api.deps import CurrentUser
from agora.api.models import (
    GooglePubSubData,
    GooglePubSubMessage,
    GooglePubSubPayload,
    Token,
)
from agora.api.render import create_context
from agora.config import settings
from agora.google_api import (
    GOOGLE_OAUTH_CLIENT_CONFIG,
    SCOPES,
    check_and_store_user_credentials,
    handle_gmail_notification,
    list_messages,
    user_credentials,
    watch_user,
)

router = APIRouter(prefix="/google", tags=["google"])


@router.get("/authorize")
def authorize(request: Request) -> RedirectResponse:
    """
    Route to authorize a user to access their Gmail account via OAuth 2.0.
    This requests consent from the user by interacting with Google's OAuth 2.0 server.

    Args:
        request (Request): The HTTP request object.
    """
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = Flow.from_client_config(
        GOOGLE_OAUTH_CLIENT_CONFIG, scopes=SCOPES, autogenerate_code_verifier=True
    )

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = request.url_for("oauth2callback")

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type="offline",
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes="true",
    )

    # Store the state so the callback can verify the auth server response.
    request.session["state"] = state
    request.session["code_verifier"] = flow.code_verifier

    return RedirectResponse(url=authorization_url)


@router.get("/oauth2callback")
async def oauth2callback(
    request: Request, background_tasks: BackgroundTasks
) -> RedirectResponse:
    """
    The callback endpoint for Google's OAuth 2.0 server response. The OAuth 2.0 server
    responds to the application by sending a request to this URL. If the user approves
    the access request, then the response contains an authorization code. If the user
    does not approve the request, the response contains an error message.

    The authorization code or error message that is returned to the web server appears
    on the query string, as shown in the following examples:

    An error response:

        https://agora.com/api/v1/google/oauth2callback?error=access_denied

    An authorization code response:

        https://agora.com/api/v1/google/oauth2callback?code=4/P7q7W91a-oMsCeLvIaQm6bTrgtp7
    """
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = request.session.get("state")

    flow = Flow.from_client_config(
        GOOGLE_OAUTH_CLIENT_CONFIG,
        scopes=SCOPES,
        state=state,
        code_verifier=request.session.get("code_verifier"),
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = request.url_for("oauth2callback")

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = str(request.url)
    if settings.FASTAPI_ENV == "development":
        authorization_response = authorization_response.replace("http://", "https://")
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in DB
    credentials = cast(Credentials, flow.credentials)
    user = await check_and_store_user_credentials(credentials)

    # Trigger background task to send watch request for user
    background_tasks.add_task(watch_user, user)

    # Generate a token for app auth
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = Token(
        access_token=security.create_access_token(
            data={"sub": user.pk}, expires_delta=access_token_expires
        )
    )

    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=f"{token.token_type.capitalize()} {token.access_token}",
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
        secure=settings.FASTAPI_ENV != "development",  # Recommended for production
    )
    return response


def get_stored_credentials(user: CurrentUser, request: Request) -> Credentials:
    """
    Retrieved stored credentials for the authorized user.

    Args:
        user (CurrentUser): The authorized user.
        request (Request): The HTTP request object.

    Raises:
        HTTPException: if no credentials stored on disk.

    Returns:
        Credentials: the user's credentials object.
    """
    try:
        credentials = user_credentials(user)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail=(
                "Oops! Invalid or expired credentials. "
                f"Go to {request.url_for('authorize')} to authorize access."
            ),
        )
    return credentials


UserCredentials = Annotated[Credentials, Depends(get_stored_credentials)]


@router.get("/revoke")
async def revoke(
    user: CurrentUser, credentials: UserCredentials, request: Request
) -> RedirectResponse:
    r = requests.post(
        "https://oauth2.googleapis.com/revoke",
        params={"token": credentials.token},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    r.raise_for_status()
    user.granted_scopes = None
    user.token = None
    user.refresh_token = None
    await user.update()

    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    return response


@router.get("/list")
def gmail_list_messages(
    request: Request,
    current_user: CurrentUser,
    credentials: UserCredentials,
    hx_request: Annotated[str | None, Header()] = None,
    query: str = "",
):
    try:
        messages = list_messages(credentials, query)
    except google_api_errors.HttpError as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occured with google's API: {e}",
        )

    context = create_context(current_user)
    context["messages"] = messages
    if hx_request:
        return templates.TemplateResponse(
            request=request, name="components/_messages.html", context=context
        )
    return templates.TemplateResponse(
        request=request, name="pages/gmail_messages.html", context=context
    )


@router.post("/webhook")
async def gmail_push_webhook(
    payload: GooglePubSubPayload, background_tasks: BackgroundTasks
):
    if payload.subscription == settings.GOOGLE_WEBHOOK_SUBSCRIPTION:
        background_tasks.add_task(handle_gmail_notification, payload)

    # Always return HTTP.200 to acknowledge notification
    return {"ack": True}


@router.post("/test-webhook")
async def test_gmail_push_webhook(
    current_user: CurrentUser, background_tasks: BackgroundTasks
):
    if not current_user.google_api_history_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Missing user's history id",
        )

    data = GooglePubSubData(
        emailAddress=current_user.email,
        historyId=current_user.google_api_history_id,
    )
    message = GooglePubSubMessage(
        data=data, messageId="1234567890", publishTime=datetime.now(timezone.utc)
    )
    payload = GooglePubSubPayload(
        subscription=settings.GOOGLE_WEBHOOK_SUBSCRIPTION, message=message
    )
    background_tasks.add_task(handle_gmail_notification, payload)
    return {"ack": True}
