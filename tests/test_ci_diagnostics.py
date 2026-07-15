from pathlib import Path

from scripts.annotate_pytest_junit import main


def test_junit_failure_becomes_single_line_annotation(
    tmp_path: Path, capsys
) -> None:
    report = tmp_path / "report.xml"
    report.write_text(
        '<testsuite><testcase name="synthetic" file="tests/example.py" line="7">'
        '<failure message="failed">first line\nsecond line</failure>'
        "</testcase></testsuite>",
        encoding="utf-8",
    )

    main(report)

    output = capsys.readouterr().out
    assert "::error file=tests/example.py,line=7,title=pytest::" in output
    assert "first line%0Asecond line" in output
    assert output.count("\n") == 1
