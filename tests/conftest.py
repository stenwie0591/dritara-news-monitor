"""Hook pytest condivisi; nessun accesso a configurazione o dati runtime."""

import os


def _workflow_escape(value: object) -> str:
    return (
        str(value)
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def _emit_failure(report) -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true" or not report.failed:
        return
    path, line_index, test_name = report.location
    annotation = (
        f"::error file={_workflow_escape(path)},line={line_index + 1},"
        f"title={_workflow_escape(test_name)}::{_workflow_escape(report.longrepr)}\n"
    )
    os.write(1, annotation.encode("utf-8"))


def pytest_runtest_logreport(report) -> None:
    """Rende i test falliti consultabili come annotazioni GitHub."""
    _emit_failure(report)


def pytest_collectreport(report) -> None:
    """Rende anche gli errori di import/collection consultabili in GitHub."""
    _emit_failure(report)
