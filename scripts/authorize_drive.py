"""
Script one-shot per autorizzare l'accesso a Google Drive via OAuth2.
Eseguire UNA VOLTA sul Mac — genera token_drive.json che va copiato sul RPi.
"""
import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from src.secret_hygiene import ensure_private_file, write_private_text

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_PATH = Path("credentials_oauth.json")
TOKEN_PATH = Path("token_drive.json")


def main() -> None:
    ensure_private_file(CREDENTIALS_PATH, required=True)
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }
    write_private_text(TOKEN_PATH, json.dumps(token_data, indent=2))
    print("✅ token_drive.json generato con successo")


if __name__ == "__main__":
    main()
