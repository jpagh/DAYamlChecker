import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from dayamlchecker.code_formatter import _collect_yaml_files


def test_formatter_collect_yaml_files_default_ignores_common_directories():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        visible = root / "visible.yml"
        git_file = root / ".git" / "hidden.yml"
        github_file = root / ".github-actions" / "ci.yml"
        sources_file = root / "sources" / "skip.yml"

        git_file.parent.mkdir(parents=True)
        github_file.parent.mkdir(parents=True)
        sources_file.parent.mkdir(parents=True)

        visible.write_text("question: visible\n", encoding="utf-8")
        git_file.write_text("question: git\n", encoding="utf-8")
        github_file.write_text("question: github\n", encoding="utf-8")
        sources_file.write_text("question: sources\n", encoding="utf-8")

        collected = _collect_yaml_files([root])

        assert collected == [visible]


def test_formatter_collect_yaml_files_can_disable_default_ignores():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        visible = root / "visible.yml"
        git_file = root / ".git" / "hidden.yml"
        github_file = root / ".github-actions" / "ci.yml"
        sources_file = root / "sources" / "skip.yml"

        git_file.parent.mkdir(parents=True)
        github_file.parent.mkdir(parents=True)
        sources_file.parent.mkdir(parents=True)

        visible.write_text("question: visible\n", encoding="utf-8")
        git_file.write_text("question: git\n", encoding="utf-8")
        github_file.write_text("question: github\n", encoding="utf-8")
        sources_file.write_text("question: sources\n", encoding="utf-8")

        collected = _collect_yaml_files([root], include_default_ignores=False)

        assert collected == sorted([visible, git_file, github_file, sources_file])


def _run_formatter(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "dayamlchecker.code_formatter", *args],
        capture_output=True,
        text=True,
    )


def test_formatter_skips_jinja_file_with_message():
    with TemporaryDirectory() as tmp:
        jinja_file = Path(tmp) / "interview.yml"
        jinja_file.write_text("---\nquestion: Hello {{ user }}\n", encoding="utf-8")

        result = _run_formatter(str(jinja_file))

        assert result.returncode == 0
        assert "Skipped (Jinja)" in result.stdout


def test_formatter_jinja_count_in_summary():
    with TemporaryDirectory() as tmp:
        jinja_file = Path(tmp) / "interview.yml"
        jinja_file.write_text("---\nquestion: Hello {{ user }}\n", encoding="utf-8")

        result = _run_formatter(str(jinja_file))

        assert "skipped (Jinja)" in result.stdout
        assert "1 skipped (Jinja)" in result.stdout


def test_formatter_jinja_not_in_summary_when_zero():
    with TemporaryDirectory() as tmp:
        regular_file = Path(tmp) / "interview.yml"
        regular_file.write_text("---\nquestion: Hello world\n", encoding="utf-8")

        result = _run_formatter(str(regular_file))

        assert "skipped (Jinja)" not in result.stdout


def test_formatter_jinja_file_not_modified():
    with TemporaryDirectory() as tmp:
        jinja_file = Path(tmp) / "interview.yml"
        original = "---\nquestion: Hello {{ user }}\ncode: |\n  x=1\n"
        jinja_file.write_text(original, encoding="utf-8")

        _run_formatter(str(jinja_file))

        assert jinja_file.read_text(encoding="utf-8") == original


def test_formatter_quiet_suppresses_jinja_message():
    with TemporaryDirectory() as tmp:
        jinja_file = Path(tmp) / "interview.yml"
        jinja_file.write_text("---\nquestion: Hello {{ user }}\n", encoding="utf-8")

        result = _run_formatter("--quiet", str(jinja_file))

        assert result.returncode == 0
        assert "Skipped (Jinja)" not in result.stdout


def test_formatter_summary_omits_zero_counts():
    with TemporaryDirectory() as tmp:
        jinja_file = Path(tmp) / "interview.yml"
        jinja_file.write_text("---\nquestion: Hello {{ user }}\n", encoding="utf-8")

        result = _run_formatter(str(jinja_file))

        # When everything is Jinja-skipped, reformatted/unchanged should not appear
        assert "reformatted" not in result.stdout
        assert "unchanged" not in result.stdout
        assert "skipped (Jinja)" in result.stdout
