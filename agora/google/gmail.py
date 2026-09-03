import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

LOGGER = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
API_SERVICE_NAME = "gmail"
API_VERSION = "v1"

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def get_credentials(credentials_dir: Path) -> Credentials:
    """
    Get the credentials for the Gmail API.
    """
    creds = None
    token_path = credentials_dir / "token.json"
    credentials_path = credentials_dir / "credentials.json"

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return creds  # type: ignore


def read_emails(credentials_dir: Path = Path(".credentials")):
    """
    Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = get_credentials(credentials_dir)
    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            LOGGER.info("No labels found.")
            return
        LOGGER.info("Labels:")
        for label in labels:
            LOGGER.info(label["name"])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        LOGGER.error(f"An error occurred: {error}")
