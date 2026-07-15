from datetime import date
from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr

from src.config import ConfigurationError, RuntimeSettings, redact_runtime_secrets


def runtime_settings(**overrides) -> RuntimeSettings:
    values = {
        "_env_file": None,
        "telegram_bot_token": SecretStr("super-secret-token"),
        "telegram_admin_chat_id": 1,
        "telegram_admin_user_id": 1,
        "telegram_community_chat_id": -100,
        "telegram_news_thread_id": 2,
        "google_drive_folder_id": "folder-1",
    }
    values.update(overrides)
    return RuntimeSettings(**values)


def test_runtime_validation_aggregates_problems() -> None:
    settings = RuntimeSettings(_env_file=None, log_level="verbose")

    with pytest.raises(ConfigurationError) as error:
        settings.validated_for_runtime()

    message = str(error.value)
    assert "TELEGRAM_BOT_TOKEN" in message
    assert "TELEGRAM_ADMIN_CHAT_ID" in message
    assert "LOG_LEVEL" in message


def test_secret_is_redacted_from_settings_repr() -> None:
    settings = runtime_settings()

    assert "super-secret-token" not in repr(settings)
    assert "**********" in repr(settings)


def test_runtime_secret_is_redacted_from_log_message() -> None:
    settings = runtime_settings()

    redacted = redact_runtime_secrets(
        "request failed at https://api.telegram.org/botsuper-secret-token/send",
        settings,
    )

    assert "super-secret-token" not in redacted
    assert "[REDACTED]" in redacted


@pytest.mark.asyncio
async def test_sender_uses_injected_settings_without_service_locator(
    monkeypatch,
) -> None:
    from src import sender_telegram

    class Response:
        def json(self):
            return {"ok": True, "result": {"message_id": 42}}

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            assert "super-secret-token" in url
            return Response()

    monkeypatch.setattr(sender_telegram, "get_settings", _unexpected_lookup)
    monkeypatch.setattr(sender_telegram.httpx, "AsyncClient", Client)

    result = await sender_telegram._send(1, "test", settings=runtime_settings())

    assert result == 42


def test_drive_uses_injected_folder_without_service_locator(monkeypatch) -> None:
    from src import drive

    files = MagicMock()
    files.list.return_value.execute.return_value = {"files": []}
    files.create.return_value.execute.return_value = {"id": "file-1"}
    service = MagicMock()
    service.files.return_value = files

    monkeypatch.setattr(drive, "get_settings", _unexpected_lookup)
    monkeypatch.setattr(drive, "_get_drive_service", lambda: service)

    result = drive.upload_csv_giornaliero(
        [], date(2026, 7, 15), settings=runtime_settings()
    )

    assert result == "file-1"
    query = files.list.call_args.kwargs["q"]
    assert "'folder-1' in parents" in query


def test_scheduler_jobs_receive_composition_root_settings(monkeypatch) -> None:
    from src import scheduler

    settings = runtime_settings()
    monkeypatch.setattr(scheduler, "get_settings", _unexpected_lookup)

    instance = scheduler.build_scheduler(settings)

    jobs = instance.get_jobs()
    injected = [job for job in jobs if "settings" in job.kwargs]
    assert injected
    assert all(job.kwargs["settings"] is settings for job in injected)


def _unexpected_lookup():
    raise AssertionError("get_settings non deve essere usato con injection esplicita")
