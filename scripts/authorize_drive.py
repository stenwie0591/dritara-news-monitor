"""
Script one-shot per autorizzare l'accesso a Google Drive via OAuth2.
Eseguire UNA VOLTA sul Mac — genera token_drive.json che va copiato sul RPi.
"""
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

flow = InstalledAppFlow.from_client_secrets_file("credentials_oauth.json", SCOPES)
creds = flow.run_local_server(port=0)

token_data = {
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "scopes": list(creds.scopes),
}

fd = os.open("token_drive.json", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as f:
    json.dump(token_data, f, indent=2)

print("✅ token_drive.json generato con successo")
