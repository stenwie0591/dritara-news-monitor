from __future__ import annotations

from pathlib import Path
import sqlite3

from alembic import command
from alembic.config import Config
import pytest
from sqlmodel import SQLModel, create_engine

import src.models  # noqa: F401
from src.schema_baseline import (
    EXPECTED_SYNTHETIC_LEGACY_FINGERPRINT,
    LegacySchemaMismatch,
    assert_expected_legacy_schema,
    schema_fingerprint,
    schema_manifest,
)


ROOT = Path(__file__).resolve().parent.parent
LEGACY_SCHEMA = ROOT / "tests" / "fixtures" / "legacy_schema.sql"


def _config(database_path: Path | None) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    if database_path is not None:
        config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    return config


def _legacy_database(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.executescript(LEGACY_SCHEMA.read_text(encoding="utf-8"))
    connection.commit()
    return connection


def _revision(connection: sqlite3.Connection) -> str | None:
    version_table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'alembic_version'"
    ).fetchone()
    if version_table is None:
        return None
    row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    return None if row is None else row[0]


def _schema_rows(connection: sqlite3.Connection) -> list[tuple]:
    return connection.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        """
    ).fetchall()


def test_fresh_upgrade_creates_current_schema_and_reaches_head(tmp_path: Path) -> None:
    database_path = tmp_path / "fresh.db"

    command.upgrade(_config(database_path), "head")

    with sqlite3.connect(database_path) as connection:
        tables = set(schema_manifest(connection)["tables"])
        assert tables == {
            "article",
            "digestlog",
            "feedsource",
            "feedstats",
            "keywordconfig",
            "keywordweighthistory",
            "publishqueue",
        }
        assert _revision(connection) == "0001_legacy_baseline"


def test_second_upgrade_is_a_schema_no_op(tmp_path: Path) -> None:
    database_path = tmp_path / "fresh.db"
    config = _config(database_path)
    command.upgrade(config, "head")

    with sqlite3.connect(database_path) as connection:
        before = _schema_rows(connection)

    command.upgrade(config, "head")

    with sqlite3.connect(database_path) as connection:
        assert _schema_rows(connection) == before
        assert _revision(connection) == "0001_legacy_baseline"


def test_fresh_upgrade_matches_declared_sqlmodel_metadata(tmp_path: Path) -> None:
    migrated_path = tmp_path / "migrated.db"
    model_path = tmp_path / "model.db"
    command.upgrade(_config(migrated_path), "head")
    model_engine = create_engine(f"sqlite:///{model_path}")
    SQLModel.metadata.create_all(model_engine)
    model_engine.dispose()

    with (
        sqlite3.connect(migrated_path) as migrated,
        sqlite3.connect(model_path) as model,
    ):
        assert schema_manifest(migrated) == schema_manifest(model)


def test_legacy_fixture_is_verified_then_stamped_without_data_loss(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "legacy.db"
    with _legacy_database(database_path) as connection:
        assert schema_fingerprint(connection) == EXPECTED_SYNTHETIC_LEGACY_FINGERPRINT
        assert_expected_legacy_schema(connection)
        before = connection.execute("SELECT * FROM feedsource").fetchall()
        assert _revision(connection) is None

    command.stamp(_config(database_path), "head")
    command.upgrade(_config(database_path), "head")

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT * FROM feedsource").fetchall() == before
        assert _revision(connection) == "0001_legacy_baseline"


def test_mismatch_fails_closed_without_writing_version_table(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "unexpected.db"
    with _legacy_database(database_path) as connection:
        connection.execute("ALTER TABLE article ADD COLUMN injected VARCHAR")
        connection.commit()
        before = _schema_rows(connection)
        changes_before = connection.total_changes

        with pytest.raises(LegacySchemaMismatch, match="Nessuna revisione"):
            assert_expected_legacy_schema(connection)

        assert connection.total_changes == changes_before
        assert _schema_rows(connection) == before
        assert _revision(connection) is None


def test_empty_database_is_not_accepted_as_legacy() -> None:
    with sqlite3.connect(":memory:") as connection:
        with pytest.raises(LegacySchemaMismatch):
            assert_expected_legacy_schema(connection)


def test_alembic_requires_an_explicit_file_database() -> None:
    with pytest.raises(RuntimeError, match="Database URL obbligatorio"):
        command.upgrade(_config(None), "head")


def test_alembic_rejects_relative_database_path() -> None:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", "sqlite:///relative.db")
    with pytest.raises(RuntimeError, match="assoluto"):
        command.upgrade(config, "head")


def test_baseline_downgrade_is_rejected_without_schema_change(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "fresh.db"
    config = _config(database_path)
    command.upgrade(config, "head")
    with sqlite3.connect(database_path) as connection:
        before = _schema_rows(connection)

    with pytest.raises(RuntimeError, match="restore"):
        command.downgrade(config, "base")

    with sqlite3.connect(database_path) as connection:
        assert _schema_rows(connection) == before
        assert _revision(connection) == "0001_legacy_baseline"
