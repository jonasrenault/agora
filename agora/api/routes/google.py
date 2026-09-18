from typing import Annotated, cast

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient import errors as google_api_errors

from agora.api.deps import CurrentSuperUser
from agora.config import settings
from agora.google_api import SCOPES, check_and_store_user_credentials, list_messages

router = APIRouter(prefix="/google", tags=["google"])


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


@router.get("/authorize")
def authorize(*, admin: CurrentSuperUser, request: Request) -> RedirectResponse:
    """
    Route to authorize a super user to access their Gmail account via OAuth 2.0.
    This requests consent from the user by interacting with Google's OAuth 2.0 server.

    Args:
        admin (CurrentSuperUser): The super user dependency, to ensure that only
            authorized super users can access this route.
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
async def oauth2callback(admin: CurrentSuperUser, request: Request) -> RedirectResponse:
    """
    The callback endpoint for Google's OAuth 2.0 server response. The OAuth 2.0 server
    responds to the application by sending a request to this URL. If the user approves
    the access request, then the response contains an authorization code. If the user
    does not approve the request, the response contains an error message.

    The authorization code or error message that is returned to the web server appears
    on the query string, as shown in the following examples:

    An error response:

        https://agora.fastapicloud.com/api/v1/google/oauth2callback?error=access_denied

    An authorization code response:

        https://agora.fastapicloud.com/api/v1/google/oauth2callback?code=4/P7q7W91a-oMsCeLvIaQm6bTrgtp7
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
    await check_and_store_user_credentials(credentials, admin)

    return RedirectResponse(url=request.url_for("gmail_list_messages"))


def get_stored_credentials(admin: CurrentSuperUser, request: Request) -> Credentials:
    """
    Retrieved stored credentials for the authorized super user.

    Args:
        admin (CurrentSuperUser): The authorized super user.
        request (Request): The HTTP request object.

    Raises:
        HTTPException: if no credentials stored on disk.

    Returns:
        Credentials: the super user's credentials object.
    """
    # Load client secrets from the server-side file.
    client_config = GOOGLE_OAUTH_CLIENT_CONFIG["web"]

    if (
        admin.token is None and admin.refresh_token is None
    ) or admin.granted_scopes is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "Oops! Invalid or expired credentials. "
                f"Go to {request.url_for('authorize')} to authorize access."
            ),
        )

    # Reconstruct the credentials object.
    credentials = Credentials(
        refresh_token=admin.refresh_token,
        scopes=admin.granted_scopes,
        token=admin.token,
        client_id=client_config.get("client_id"),
        client_secret=client_config.get("client_secret"),
        token_uri=client_config.get("token_uri"),
    )

    return credentials


SuperUserCredentials = Annotated[Credentials, Depends(get_stored_credentials)]


@router.get("/clear")
async def clear_credentials(admin: CurrentSuperUser) -> RedirectResponse:
    admin.granted_scopes = None
    admin.token = None
    admin.refresh_token = None
    await admin.update()
    return RedirectResponse(url="/")


@router.get("/revoke")
async def revoke(credentials: SuperUserCredentials, request: Request) -> RedirectResponse:
    r = requests.post(
        "https://oauth2.googleapis.com/revoke",
        params={"token": credentials.token},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    r.raise_for_status()
    return RedirectResponse(url=request.url_for("clear_credentials"))


@router.get("/list")
def gmail_list_messages(credentials: SuperUserCredentials, query: str = ""):
    try:
        return list_messages(credentials, query)
    except google_api_errors.HttpError as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occured with google's API: {e}",
        )
