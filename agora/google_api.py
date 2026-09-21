import logging

from aredis_om import NotFoundError
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from agora.api.crud import get_or_create_user
from agora.api.models import GmailMessage, GooglePubSubPayload, User, UserCreate
from agora.automation import run_automation_for_user
from agora.config import settings

LOGGER = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
API_SERVICE_NAME = "gmail"
API_VERSION = "v1"
GOOGLE_OAUTH_CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "project_id": settings.GOOGLE_OAUTH_PROJECT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uris": [
            "http://127.0.0.1:8000/api/v1/google/oauth2callback",
            "https://agora-production-dba8.up.railway.app/api/v1/google/oauth2callback",
            "http://localhost/api/v1/google/oauth2callback",
        ],
    }
}


def user_credentials(user: User) -> Credentials:
    if (user.token is None and user.refresh_token is None) or user.granted_scopes is None:
        raise ValueError("Invalid credentials")

    client_config = GOOGLE_OAUTH_CLIENT_CONFIG["web"]
    credentials = Credentials(
        refresh_token=user.refresh_token,
        scopes=user.granted_scopes,
        token=user.token,
        client_id=client_config.get("client_id"),
        client_secret=client_config.get("client_secret"),
        token_uri=client_config.get("token_uri"),
    )
    return credentials


async def check_and_store_user_credentials(credentials: Credentials) -> User:
    """
    Check credentials returned by OAuth 2.0 endpoint and store them in the DB.

    Args:
        credentials (Credentials): client credentials

    Raises:
        HTTPException: if granted_scopes are missing.

    Returns:
        User: the user authentified with google OAuth.
    """
    # Check required scopes have been granted
    for scope in SCOPES:
        if credentials.granted_scopes is None or scope not in credentials.granted_scopes:
            raise HTTPException(
                status_code=400, detail=f"Missing required scope: {scope}"
            )

    # Call Gmail API to get email and history id
    service = build_service(credentials)
    result = service.users().getProfile(userId="me").execute()

    # Store credentials in user model
    user_in = UserCreate(
        email=result.get("emailAddress"),
        google_api_history_id=result.get("historyId"),
        token=credentials.token,
        granted_scopes=credentials.granted_scopes,
        refresh_token=credentials.refresh_token,
    )
    user = await get_or_create_user(user_in)
    return user


def build_service(credentials: Credentials):
    return build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials, cache_discovery=False
    )


def list_messages(credentials: Credentials, query: str) -> list[GmailMessage]:
    service = build_service(credentials)
    results = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], q=query)
        .execute()
    )
    ids = []
    ids.extend(results.get("messages", []))

    while "nextPageToken" in results:
        page_token = results["nextPageToken"]
        results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], q=query, pageToken=page_token)
            .execute()
        )
        ids.extend(results.get("messages", []))

    messages: list[GmailMessage] = []
    for message_id in ids:
        message = (
            service.users()
            .messages()
            .get(userId="me", id=message_id["id"], format="full")
            .execute()
        )

        # Extract headers
        payload = message.get("payload", {})
        headers = payload.get("headers", [])
        snippet = message.get("snippet", "")
        subject = "No Subject"
        sender = "Unknown"

        for header in headers:
            if header["name"] == "Subject":
                subject = header["value"]
            elif header["name"] == "From":
                sender = header["value"]

        messages.append(GmailMessage(sender=sender, subject=subject, snippet=snippet))

    return messages


async def handle_gmail_notification(payload: GooglePubSubPayload):
    # find user in DB
    LOGGER.info(f"Handling Gmail push notification for {payload.message.data.email}.")
    try:
        user: User = await User.find(
            User.google_api_email == payload.message.data.email
        ).first()  # type: ignore
    except NotFoundError:
        LOGGER.error(f"User {payload.message.data.email} not found.", exc_info=True)
        raise NotFoundError(f"User {payload.message.data.email} not found.")

    # udpate user history id
    await user.update(google_api_history_id=payload.message.data.history_id)

    # check if user has agora notification email in inbox
    credentials = user_credentials(user)
    messages = list_messages(credentials, "")
    has_notification = False
    for message in messages:
        if message.sender == settings.AGORA_NOTIFICATIONS_SENDER:
            has_notification = True
            break

    if not has_notification:
        LOGGER.info("No agora portal notification found in user's inbox.")
        return

    # trigger an automation run
    await run_automation_for_user(user, headless=True, dry_run=False)
