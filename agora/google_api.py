from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from agora.api.models import User

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
API_SERVICE_NAME = "gmail"
API_VERSION = "v1"


async def check_and_store_user_credentials(credentials: Credentials, user: User):
    """
    Check credentials returned by OAuth 2.0 endpoint and store them on the user model.

    Args:
        credentials (Credentials): client credentials
        admin (User): user model

    Raises:
        HTTPException: if granted_scopes are missing.
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
    update_data = {
        "token": credentials.token,
        "granted_scopes": credentials.granted_scopes,
        "google_api_email": result.get("emailAddress", None),
        "google_api_history_id": result.get("historyId", None),
    }

    # Refresh token is only provided by Google on the first authorization.
    # Don't erase it when user has already authorized the app and refresh token is
    # not provided by Google.
    if credentials.refresh_token is not None:
        update_data["refresh_token"] = credentials.refresh_token
    await user.update(**update_data)


def build_service(credentials: Credentials):
    return build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials, cache_discovery=False
    )


def list_messages(credentials: Credentials, query: str):
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

    messages = []
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

        messages.append({"subject": subject, "sender": sender, "snippet": snippet})
    return messages
