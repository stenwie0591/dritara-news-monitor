"""Configurazione runtime centralizzata e tipizzata.

Il modulo è import-safe: le credenziali vengono validate soltanto quando un
entrypoint che ne ha bisogno viene avviato. Test, lint e migrazioni possono
quindi girare anche senza un file `.env`.
"""

from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigurationError(RuntimeError):
    """Configurazione obbligatoria assente o non valida."""


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: SecretStr | None = None
    telegram_admin_chat_id: int | None = None
    telegram_admin_user_id: int | None = None
    telegram_community_chat_id: int | None = None
    telegram_news_thread_id: int | None = None
    google_drive_folder_id: str | None = None
    log_level: str = "INFO"

    def validated_for_runtime(self) -> Self:
        """Valida in un solo passaggio tutto ciò che serve al processo principale."""
        required = {
            "TELEGRAM_BOT_TOKEN": self.telegram_bot_token,
            "TELEGRAM_ADMIN_CHAT_ID": self.telegram_admin_chat_id,
            "TELEGRAM_ADMIN_USER_ID": self.telegram_admin_user_id,
            "TELEGRAM_COMMUNITY_CHAT_ID": self.telegram_community_chat_id,
            "TELEGRAM_NEWS_THREAD_ID": self.telegram_news_thread_id,
        }
        problems = [name for name, value in required.items() if value is None]
        if self.telegram_bot_token is not None and not self.telegram_token_value.strip():
            problems.append("TELEGRAM_BOT_TOKEN (vuoto)")
        if self.log_level.upper() not in {
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }:
            problems.append(f"LOG_LEVEL (non valido: {self.log_level})")
        if problems:
            raise ConfigurationError(
                "Configurazione runtime non valida: " + ", ".join(problems)
            )
        return self

    def require_telegram(self) -> None:
        """Compatibilità: valida la configurazione richiesta dal runtime Telegram."""
        self.validated_for_runtime()

    @property
    def telegram_token_value(self) -> str:
        if self.telegram_bot_token is None:
            return ""
        return self.telegram_bot_token.get_secret_value()


def redact_runtime_secrets(message: object, settings: RuntimeSettings) -> str:
    """Redige credenziali note prima che un messaggio raggiunga i sink di log."""
    text = str(message)
    secrets = [settings.telegram_token_value]
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text


@lru_cache(maxsize=1)
def get_settings() -> RuntimeSettings:
    """Compatibility factory; il composition root deve iniettare il risultato."""
    return RuntimeSettings()
