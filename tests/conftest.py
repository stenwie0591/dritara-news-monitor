"""Hook pytest condivisi; nessun accesso a configurazione o dati runtime."""

import os


def _workflow_escape(value: object) -> str:
    return (
        str(value)
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def pytest_runtest_logreport(report) -> None:
    """Rende i failure consultabili come annotazioni GitHub senza plugin esterni."""
    if os.environ.get("GITHUB_ACTIONS") != "true" or not report.failed:
        return
    path, line_index, test_name = report.location
    print(
        f"::error file={_workflow_escape(path)},line={line_index + 1},"
        f"title={_workflow_escape(test_name)}::{_workflow_escape(report.longrepr)}"
    )
