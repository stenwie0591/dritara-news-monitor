import stat
from pathlib import Path

import pytest
from loguru import logger
from pydantic import SecretStr

from main import configure_logging
from src.config import RuntimeSettings
from src.secret_hygiene import (
    SecretPermissionError,
    ensure_private_directory,
    ensure_private_file,
    read_private_text,
    validate_runtime_secret_modes,
    write_private_text,
)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _settings() -> RuntimeSettings:
    return RuntimeSettings(
        _env_file=None,
        telegram_bot_token=SecretStr("synthetic-secret-token"),
        telegram_admin_chat_id=1,
        telegram_admin_user_id=1,
        telegram_community_chat_id=-100,
        telegram_news_thread_id=2,
    )


def test_optional_secret_files_may_be_absent(tmp_path: Path) -> None:
    validate_runtime_secret_modes(tmp_path)


def test_private_file_requires_exact_mode(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("SYNTHETIC=value", encoding="utf-8")
    path.chmod(0o640)

    with pytest.raises(SecretPermissionError, match="0600"):
        ensure_private_file(path)

    path.chmod(0o600)
    assert ensure_private_file(path)


def test_private_file_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_text("synthetic", encoding="utf-8")
    target.chmod(0o600)
    link = tmp_path / "token_drive.json"
    link.symlink_to(target)

    with pytest.raises(SecretPermissionError, match="symlink"):
        ensure_private_file(link)


def test_private_directory_requires_exact_mode(tmp_path: Path) -> None:
    directory = tmp_path / "backup"
    directory.mkdir(mode=0o755)
    directory.chmod(0o755)

    with pytest.raises(SecretPermissionError, match="0700"):
        ensure_private_directory(directory)

    directory.chmod(0o700)
    assert ensure_private_directory(directory)


def test_private_writer_repairs_existing_mode(tmp_path: Path) -> None:
    path = tmp_path / "token_drive.json"
    path.write_text("old synthetic content", encoding="utf-8")
    path.chmod(0o644)

    write_private_text(path, "new synthetic content")

    assert _mode(path) == 0o600
    assert path.read_text(encoding="utf-8") == "new synthetic content"


def test_private_reader_rejects_permissive_file(tmp_path: Path) -> None:
    path = tmp_path / "token_drive.json"
    path.write_text("synthetic", encoding="utf-8")
    path.chmod(0o644)

    with pytest.raises(SecretPermissionError, match="0600"):
        read_private_text(path)

    path.chmod(0o600)
    assert read_private_text(path) == "synthetic"


def test_logging_redacts_token_and_secures_sink(tmp_path: Path) -> None:
    log_path = tmp_path / "runtime-logs" / "monitor.log"
    configure_logging(_settings(), log_path=log_path)
    try:
        logger.error(
            "provider failed at "
            "https://api.telegram.org/botsynthetic-secret-token/sendMessage"
        )
        content = log_path.read_text(encoding="utf-8")
    finally:
        logger.remove()

    assert "synthetic-secret-token" not in content
    assert "[REDACTED]" in content
    assert _mode(log_path.parent) == 0o700
    assert _mode(log_path) == 0o600
