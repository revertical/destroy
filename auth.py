"""Shared auth helpers used by every example.

Two services are used in these examples:

1. Slides API (build("slides", "v1")) -- reads/writes presentation content.
2. Drive API (build("drive", "v3")) -- creates presentations, since a Slides
   deck is actually a Drive file with the mime type
   application/vnd.google-apps.presentation.

Setup (needed once):

1. Go to https://console.cloud.google.com and enable both APIs:
   - Google Slides API
   - Google Drive API
2. Create OAuth credentials -> Desktop app -> download JSON, save as
   credentials.json in this folder.
3. Run any example. A browser opens, you log in, and a token.json file is
   saved so you won't be prompted again.
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Slides content + Drive (needed to create new files on your behalf).
# Note: the Slides scope is "presentations" (plural, like the API) — the
# singular "presentation" is not a valid scope and Google rejects it.
SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive",
]

CLIENT_SECRETS = "credentials.json"
TOKEN = "token.json"


def get_credentials():
    """Return valid OAuth2 credentials, refreshing/capturing as needed."""
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS):
                raise FileNotFoundError(
                    f"{CLIENT_SECRETS} not found. Create OAuth credentials in the "
                    "Google Cloud console and save the JSON here."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
    return creds


def get_slides_service():
    return build("slides", "v1", credentials=get_credentials())


def get_drive_service():
    return build("drive", "v3", credentials=get_credentials())