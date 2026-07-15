"""
drive.py — Integrazione Google Drive.
Funzioni:
  - upload_csv_giornaliero: carica CSV articoli del giorno
  - upload_sqlite_backup: carica backup SQLite (solo domenica)
"""

import csv
import io
import json
from datetime import date
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from loguru import logger

from src.config import RuntimeSettings, get_settings
from src.secret_hygiene import read_private_text, write_private_text

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = Path("token_drive.json")


def _safe_csv_cell(value) -> str:
    """Neutralizza valori che un foglio di calcolo può eseguire come formule."""
    text = "" if value is None else str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


def _get_drive_service():
    """Restituisce un client Drive autenticato, rinnovando il token se necessario."""
    token_data = json.loads(read_private_text(TOKEN_PATH))

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )

    # Rinnova il token se scaduto
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Salva il token aggiornato
            token_data["token"] = creds.token
            write_private_text(TOKEN_PATH, json.dumps(token_data, indent=2))
            logger.info("Token Drive rinnovato")
        else:
            raise RuntimeError(
                "Token Drive scaduto e non rinnovabile. "
                "Riesegui scripts/authorize_drive.py sul Mac."
            )

    return build("drive", "v3", credentials=creds)


def upload_csv_giornaliero(
    articles: list,
    today: date,
    *,
    settings: RuntimeSettings | None = None,
) -> str | None:
    """
    Genera e carica su Drive il CSV degli articoli rilevanti del giorno.
    Ritorna il file ID Drive o None in caso di errore.
    """
    folder_id = (settings or get_settings()).google_drive_folder_id
    if not folder_id:
        logger.warning("GOOGLE_DRIVE_FOLDER_ID non configurato — skip upload CSV")
        return None

    try:
        # Genera CSV in memoria
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "data",
                "titolo",
                "url",
                "feed",
                "sezione",
                "score",
                "keyword_matches",
                "stato",
            ]
        )
        for a in articles:
            writer.writerow(
                [
                    today.isoformat(),
                    _safe_csv_cell(a.get("title", "")),
                    _safe_csv_cell(a.get("url", "")),
                    _safe_csv_cell(a.get("feed_name", "")),
                    _safe_csv_cell(a.get("section", "")),
                    a.get("score", 0),
                    _safe_csv_cell(", ".join(a.get("keyword_matches", []))),
                    _safe_csv_cell(a.get("status", "pending")),
                ]
            )

        content = output.getvalue().encode("utf-8")
        filename = f"dritara_{today.isoformat()}.csv"

        service = _get_drive_service()

        # Controlla se esiste già un file con lo stesso nome (per sovrascrivere)
        existing = (
            service.files()
            .list(
                q=f"name='{filename}' and '{folder_id}' in parents and trashed=false",
                fields="files(id, name)",
            )
            .execute()
        )

        media = MediaIoBaseUpload(
            io.BytesIO(content),
            mimetype="text/csv",
            resumable=False,
        )

        if existing["files"]:
            # Aggiorna file esistente
            file_id = existing["files"][0]["id"]
            service.files().update(
                fileId=file_id,
                media_body=media,
            ).execute()
            logger.info(f"CSV aggiornato su Drive: {filename}")
        else:
            # Crea nuovo file
            metadata = {"name": filename, "parents": [folder_id]}
            result = (
                service.files()
                .create(
                    body=metadata,
                    media_body=media,
                    fields="id",
                )
                .execute()
            )
            file_id = result["id"]
            logger.info(f"CSV caricato su Drive: {filename} (id={file_id})")

        return file_id

    except Exception as e:
        logger.error(f"Errore upload CSV Drive: {e}")
        return None


def upload_sqlite_backup(
    db_path: Path,
    today: date,
    *,
    settings: RuntimeSettings | None = None,
) -> str | None:
    """
    Carica una copia del DB SQLite su Drive.
    Da chiamare solo la domenica.
    Ritorna il file ID Drive o None in caso di errore.
    """
    folder_id = (settings or get_settings()).google_drive_folder_id
    if not folder_id:
        logger.warning("GOOGLE_DRIVE_FOLDER_ID non configurato — skip backup SQLite")
        return None

    if not db_path.exists():
        logger.error(f"DB non trovato: {db_path}")
        return None

    try:
        filename = f"dritara_backup_{today.isoformat()}.db"
        service = _get_drive_service()

        with open(db_path, "rb") as f:
            content = f.read()

        media = MediaIoBaseUpload(
            io.BytesIO(content),
            mimetype="application/octet-stream",
            resumable=True,
        )

        metadata = {"name": filename, "parents": [folder_id]}
        result = (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id",
            )
            .execute()
        )

        file_id = result["id"]
        logger.info(f"Backup SQLite caricato su Drive: {filename} (id={file_id})")
        return file_id

    except Exception as e:
        logger.error(f"Errore backup SQLite Drive: {e}")
        return None
