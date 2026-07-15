from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import make_url
from sqlmodel import SQLModel

# Registra le tabelle nella metadata senza importare src.database o il suo
# engine globale. L'import è intenzionalmente side-effect free rispetto al DB.
import src.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _explicit_database_url() -> str:
    cli_url = context.get_x_argument(as_dictionary=True).get("db_url")
    configured_url = config.get_main_option("sqlalchemy.url")
    database_url = cli_url or configured_url
    if not database_url:
        raise RuntimeError(
            "Database URL obbligatorio: usa -x db_url=sqlite:////path/copia.db "
            "oppure impostalo programmaticamente nella Config Alembic."
        )

    parsed = make_url(database_url)
    if parsed.get_backend_name() != "sqlite":
        raise RuntimeError("M02 supporta esclusivamente URL SQLite espliciti.")
    if parsed.database in {None, "", ":memory:"}:
        raise RuntimeError(
            "Usa un file SQLite temporaneo esplicito; :memory: non è supportato "
            "dal migration environment."
        )
    if not Path(parsed.database).is_absolute():
        raise RuntimeError(
            "Il path SQLite deve essere assoluto per evitare di migrare il "
            "file sbagliato."
        )
    return database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_explicit_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _explicit_database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
