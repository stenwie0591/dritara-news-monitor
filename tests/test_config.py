import pytest
from pydantic import SecretStr

from src.config import ConfigurationError, RuntimeSettings


def test_settings_are_import_safe_without_secrets() -> None:
    settings = RuntimeSettings(_env_file=None)
    assert settings.telegram_bot_token is None
    assert settings.telegram_admin_chat_id is None


def test_telegram_validation_lists_missing_fields() -> None:
    settings = RuntimeSettings(_env_file=None)
    with pytest.raises(ConfigurationError, match="TELEGRAM_BOT_TOKEN"):
        settings.require_telegram()


def test_telegram_validation_accepts_complete_settings() -> None:
    settings = RuntimeSettings(
        _env_file=None,
        telegram_bot_token=SecretStr("token"),
        telegram_admin_chat_id=1,
        telegram_admin_user_id=1,
        telegram_community_chat_id=-100,
        telegram_news_thread_id=2,
    )
    settings.require_telegram()
    assert settings.telegram_token_value == "token"
