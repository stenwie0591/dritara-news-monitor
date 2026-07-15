#!/usr/bin/env python3
"""Converte failure JUnit sintetici in annotazioni GitHub Actions."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _escape(value: object) -> str:
    return (
        str(value)
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def main(path: Path) -> None:
    root = ET.parse(path).getroot()
    emitted = False
    for case in root.iter("testcase"):
        problem = case.find("failure")
        if problem is None:
            problem = case.find("error")
        if problem is None:
            continue
        emitted = True
        name = case.get("name", "pytest")
        location = case.get("file", "tests")
        line = case.get("line", "1")
        detail = problem.text or problem.get("message", "pytest failed")
        print(
            f"::error file={_escape(location)},line={line},title=pytest::"
            f"{_escape(name)}%0A{_escape(detail)}"
        )
    if not emitted:
        print("::error title=pytest::Failure senza testcase JUnit disponibile")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
