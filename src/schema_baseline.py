"""Fingerprint read-only dello schema SQLite legacy noto.

Il fingerprint è semantico: usa tabelle, colonne, foreign key, indici, viste e
trigger, non il testo SQL formattato da una particolare versione SQLite. Non
scrive mai sul database. Il runner che verifica e stampa la revisione appartiene
a M02.02; M02.01 espone soltanto la primitive fail-closed.
"""

from __future__ import annotations

from hashlib import sha256
import json
import sqlite3
from typing import Any


class LegacySchemaMismatch(RuntimeError):
    """Lo schema non coincide con la fixture legacy sintetica autorizzata."""


# Calcolato dalla fixture versionata tests/fixtures/legacy_schema.sql. Il valore
# viene verificato da test dedicati e non deve essere rigenerato a runtime.
EXPECTED_SYNTHETIC_LEGACY_FINGERPRINT = (
    "b6f71febc4673486978f4d2e8ba1cf6f2ce872e643f14cd7ce8405a7984c3b24"
)


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _rows(connection: sqlite3.Connection, pragma: str) -> list[sqlite3.Row]:
    return list(connection.execute(pragma).fetchall())


def schema_manifest(connection: sqlite3.Connection) -> dict[str, Any]:
    """Restituisce una rappresentazione deterministica e read-only."""

    previous_factory = connection.row_factory
    connection.row_factory = sqlite3.Row
    try:
        objects = _rows(
            connection,
            """
            SELECT type, name, tbl_name, sql
            FROM sqlite_master
            WHERE name NOT LIKE 'sqlite_%'
              AND name != 'alembic_version'
            ORDER BY type, name
            """,
        )
        table_names = sorted(row["name"] for row in objects if row["type"] == "table")

        tables: dict[str, Any] = {}
        for table_name in table_names:
            quoted = _quote_identifier(table_name)
            columns = [
                {
                    "name": row["name"],
                    "type": (row["type"] or "").upper(),
                    "notnull": bool(row["notnull"]),
                    "default": row["dflt_value"],
                    "pk": int(row["pk"]),
                }
                for row in _rows(connection, f"PRAGMA table_info({quoted})")
            ]
            foreign_keys = sorted(
                (
                    {
                        "from": row["from"],
                        "to_table": row["table"],
                        "to": row["to"],
                        "on_update": row["on_update"],
                        "on_delete": row["on_delete"],
                        "match": row["match"],
                    }
                    for row in _rows(connection, f"PRAGMA foreign_key_list({quoted})")
                ),
                key=lambda item: (item["from"], item["to_table"], item["to"]),
            )

            indexes = []
            for row in _rows(connection, f"PRAGMA index_list({quoted})"):
                index_name = row["name"]
                index_columns = [
                    info["name"]
                    for info in _rows(
                        connection,
                        f"PRAGMA index_info({_quote_identifier(index_name)})",
                    )
                ]
                indexes.append(
                    {
                        "name": "<auto>" if row["origin"] != "c" else index_name,
                        "columns": index_columns,
                        "unique": bool(row["unique"]),
                        "origin": row["origin"],
                        "partial": bool(row["partial"]),
                    }
                )
            indexes.sort(
                key=lambda item: (
                    item["name"],
                    item["columns"],
                    item["origin"],
                )
            )
            tables[table_name] = {
                "columns": columns,
                "foreign_keys": foreign_keys,
                "indexes": indexes,
            }

        auxiliary = [
            {
                "type": row["type"],
                "name": row["name"],
                "table": row["tbl_name"],
                "sql": " ".join((row["sql"] or "").split()),
            }
            for row in objects
            if row["type"] in {"view", "trigger"}
        ]
        return {"tables": tables, "auxiliary": auxiliary}
    finally:
        connection.row_factory = previous_factory


def schema_fingerprint(connection: sqlite3.Connection) -> str:
    payload = json.dumps(
        schema_manifest(connection),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def assert_expected_legacy_schema(connection: sqlite3.Connection) -> str:
    """Verifica lo schema senza scritture e restituisce il fingerprint."""

    actual = schema_fingerprint(connection)
    expected = EXPECTED_SYNTHETIC_LEGACY_FINGERPRINT
    if actual != expected:
        raise LegacySchemaMismatch(
            "Schema SQLite non riconosciuto: fingerprint "
            f"{actual}, atteso {expected}. Nessuna revisione è stata applicata."
        )
    return actual
