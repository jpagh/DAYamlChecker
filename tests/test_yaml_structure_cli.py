import io
import re
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dayamlchecker._files import _collect_yaml_files
from dayamlchecker.__main__ import main as package_main
from dayamlchecker.yaml_structure import main, process_file


def test_collect_yaml_files_recurses_directories_and_dedupes():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested = root / "nested"
        nested.mkdir()

        first = root / "a.yml"
        second = nested / "b.yaml"
        other = nested / "ignore.txt"

        first.write_text("question: one\n", encoding="utf-8")
        second.write_text("question: two\n", encoding="utf-8")
        other.write_text("not yaml\n", encoding="utf-8")

        collected = _collect_yaml_files([root, second])

        assert collected == [first, second]


def test_collect_yaml_files_default_ignores_common_directories():
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


def test_collect_yaml_files_can_disable_default_ignores():
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


# ---------------------------------------------------------------------------
# CLI (main()) / process_file() integration tests
# ---------------------------------------------------------------------------


def test_cli_valid_file_exits_zero():
    with TemporaryDirectory() as tmp:
        good = Path(tmp) / "good.yml"
        good.write_text("---\nquestion: Hello\nfield: my_var\n", encoding="utf-8")
        assert process_file(str(good)) == "ok"


def test_cli_no_files_found_exits_nonzero():
    with TemporaryDirectory() as tmp:
        # Write a text file, not YAML — _collect_yaml_files skips it, main() returns 1
        txt = Path(tmp) / "readme.txt"
        txt.write_text("hello\n", encoding="utf-8")
        with patch("sys.argv", ["dayamlchecker", str(txt)]):
            assert main() == 1


def test_cli_jinja_file_prints_ok_jinja():
    with TemporaryDirectory() as tmp:
        jinja_file = Path(tmp) / "interview.yml"
        jinja_file.write_text(
            "# use jinja\n---\nquestion: Hello {{ user }}\n", encoding="utf-8"
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(jinja_file))
        assert result == "ok"
        assert "ok (jinja)" in buf.getvalue()


def test_cli_check_all_flag_includes_git_dirs():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        git_dir = root / ".git"
        git_dir.mkdir()
        git_file = git_dir / "hidden.yml"
        git_file.write_text("---\nquestion: git\nfield: x\n", encoding="utf-8")
        # --check-all maps to include_default_ignores=False
        collected = _collect_yaml_files([root], include_default_ignores=False)
        assert git_file in collected
        assert process_file(str(git_file)) == "ok"


def test_cli_jinja_file_default_mode_prints_ok_status():
    with TemporaryDirectory() as tmp:
        jinja_file = Path(tmp) / "interview.yml"
        jinja_file.write_text(
            "# use jinja\n---\nquestion: Hello {{ user }}\n", encoding="utf-8"
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(jinja_file))
        assert result == "ok"
        output = buf.getvalue()
        assert "ok (jinja)" in output
        assert "interview.yml" in output


def test_cli_file_with_errors_reports_error_status():
    """process_file returns 'error' and prints an errors summary line."""
    with TemporaryDirectory() as tmp:
        bad = Path(tmp) / "bad.yml"
        bad.write_text("---\nnot_a_real_key: hello\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(bad))
        assert result == "error"
        output = buf.getvalue()
        assert re.search(r"errors \(\d+\):.*bad\.yml", output)
        assert "[E301]" in output


def test_cli_file_with_warnings_reports_warning_status():
    with TemporaryDirectory() as tmp:
        warning_file = Path(tmp) / "warning.yml"
        warning_file.write_text(
            "---\n"
            "question: Hello\n"
            "fields:\n"
            "  - Preferred salutation: preferred_salutation\n"
            "  - Follow up: follow_up\n"
            "    show if:\n"
            '      code: preferred_salutation == "Ms."\n',
            encoding="utf-8",
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(warning_file))
        assert result == "warning"
        output = buf.getvalue()
        assert re.search(r"warnings \(\d+\):.*warning\.yml", output)
        assert "[W410]" in output
        assert "errors" not in output.lower()


def test_cli_file_with_conventions_reports_convention_status():
    with TemporaryDirectory() as tmp:
        convention_file = Path(tmp) / "convention.yml"
        convention_file.write_text(
            "---\n"
            "question: Total fruit\n"
            "fields:\n"
            "  - Apples: number_apples\n"
            "    datatype: integer\n"
            "  - Oranges: number_oranges\n"
            "    datatype: integer\n"
            "validation code: |\n"
            "  if number_apples + number_oranges != 10:\n"
            "    raise Exception('Bad total')\n",
            encoding="utf-8",
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(convention_file))
        assert result == "warning"
        output = buf.getvalue()
        assert re.search(r"conventions \(\d+\):.*convention\.yml", output)
        assert "[C101]" in output
        assert "warnings (" not in output
        assert "errors (" not in output


def test_cli_main_exits_nonzero_when_any_file_has_errors():
    with TemporaryDirectory() as tmp:
        bad = Path(tmp) / "bad.yml"
        bad.write_text("---\nnot_a_real_key: hello\n", encoding="utf-8")

        with patch("sys.argv", ["dayamlchecker", str(bad)]):
            assert main() == 1


def test_cli_main_exits_zero_when_file_has_only_warnings():
    with TemporaryDirectory() as tmp:
        warning_file = Path(tmp) / "warning.yml"
        warning_file.write_text(
            "---\n"
            "question: Hello\n"
            "fields:\n"
            "  - Preferred salutation: preferred_salutation\n"
            "  - Follow up: follow_up\n"
            "    show if:\n"
            '      code: preferred_salutation == "Ms."\n',
            encoding="utf-8",
        )
        buf = io.StringIO()

        with redirect_stdout(buf):
            with patch("sys.argv", ["dayamlchecker", str(warning_file)]):
                result = main()

        assert result == 0
        output = buf.getvalue()
        assert "1 warnings" in output
        assert "0 errors" in output


def test_cli_jinja_file_with_bad_key_reports_errors():
    """Errors in the Jinja-rendered content must still be caught and reported.

    This is a companion to test_cli_jinja_file_default_mode_prints_ok_status:
    it verifies that the Jinja pre-processing path (preprocess_jinja -> recursive
    find_errors_from_string call) doesn't silently discard validation errors.
    """
    with TemporaryDirectory() as tmp:
        jinja_file = Path(tmp) / "bad_jinja.yml"
        jinja_file.write_text(
            "# use jinja\n---\nnot_a_real_key: hello\n", encoding="utf-8"
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(jinja_file))
        assert result == "error"
        output = buf.getvalue()
        assert re.search(r"errors \(\d+\).*bad_jinja\.yml", output)
        assert "[E301]" in output


def test_cli_process_file_skips_known_da_files():
    """process_file returns 'skipped' for known DA helper files like docstring.yml."""
    with TemporaryDirectory() as tmp:
        skipped = Path(tmp) / "docstring.yml"
        skipped.write_text(
            "this is not valid yaml interview content\n", encoding="utf-8"
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(skipped))
        assert result == "skipped"
        assert "skipped" in buf.getvalue()


def test_cli_process_file_quiet_skips_no_output():
    """process_file with quiet=True suppresses output for skipped files."""
    with TemporaryDirectory() as tmp:
        skipped = Path(tmp) / "docstring.yml"
        skipped.write_text("ignored\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(skipped), quiet=True)
        assert result == "skipped"
        assert buf.getvalue() == ""


def test_cli_process_file_quiet_ok_no_output():
    """process_file with quiet=True suppresses output for ok files."""
    with TemporaryDirectory() as tmp:
        good = Path(tmp) / "good.yml"
        good.write_text("---\nquestion: Hello\nfield: my_var\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(good), quiet=True)
        assert result == "ok"
        assert buf.getvalue() == ""


def test_cli_main_no_summary_flag():
    """--no-summary flag suppresses the summary line."""
    with TemporaryDirectory() as tmp:
        good = Path(tmp) / "good.yml"
        good.write_text("---\nquestion: Hello\nfield: my_var\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch("sys.argv", ["dayamlchecker", "--no-summary", str(good)]):
                result = main()
        assert result == 0
        assert "summary" not in buf.getvalue().lower()


def test_cli_main_quiet_flag():
    """--quiet flag suppresses all non-error output."""
    with TemporaryDirectory() as tmp:
        good = Path(tmp) / "good.yml"
        good.write_text("---\nquestion: Hello\nfield: my_var\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch("sys.argv", ["dayamlchecker", "--quiet", str(good)]):
                result = main()
        assert result == 0
        assert buf.getvalue().strip() == ""


def test_cli_main_summary_shows_counts():
    """Summary line shows counts for ok, errors, skipped."""
    with TemporaryDirectory() as tmp:
        good = Path(tmp) / "good.yml"
        good.write_text("---\nquestion: Hello\nfield: my_var\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch("sys.argv", ["dayamlchecker", str(good)]):
                main()
        output = buf.getvalue()
        assert "Summary:" in output
        assert "1 ok" in output


def test_cli_main_summary_counts_skipped_files():
    with TemporaryDirectory() as tmp:
        skipped = Path(tmp) / "good.yml"
        skipped.write_text("---\nquestion: Hello\nfield: my_var\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch(
                "dayamlchecker.yaml_structure.process_file", return_value="skipped"
            ):
                with patch("sys.argv", ["dayamlchecker", str(skipped)]):
                    result = main()

        assert result == 0
        assert "1 skipped" in buf.getvalue()


def test_cli_display_falls_back_to_absolute_path_when_not_under_base():
    with TemporaryDirectory() as base_tmp, TemporaryDirectory() as other_tmp:
        base = Path(base_tmp)
        outside = Path(other_tmp) / "outside.yml"
        outside.write_text("---\nquestion: Hello\nfield: my_var\n", encoding="utf-8")
        buf = io.StringIO()

        with redirect_stdout(buf):
            with patch(
                "dayamlchecker.yaml_structure._collect_yaml_files",
                return_value=[outside],
            ):
                with patch("sys.argv", ["dayamlchecker", str(base)]):
                    result = main()

        assert result == 0
        assert str(outside.resolve()) in buf.getvalue()


def test_cli_display_path_used_in_output():
    """process_file uses display_path when provided."""
    with TemporaryDirectory() as tmp:
        good = Path(tmp) / "good.yml"
        good.write_text("---\nquestion: Hello\nfield: my_var\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(good), display_path="custom/path.yml")
        assert result == "ok"
        assert "custom/path.yml" in buf.getvalue()


def test_cli_default_omits_real_error_prefix():
    """process_file omits the REAL ERROR prefix by default on non-experimental errors."""
    with TemporaryDirectory() as tmp:
        bad = Path(tmp) / "bad.yml"
        bad.write_text("---\nnot_a_real_key: hello\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = process_file(str(bad))
        assert result == "error"
        output = buf.getvalue()
        assert "[E301]" in output
        assert "REAL ERROR" not in output


def test_cli_show_experimental_flag_via_main():
    """--show-experimental adds the REAL ERROR prefix through the main() entry point."""
    with TemporaryDirectory() as tmp:
        bad = Path(tmp) / "bad.yml"
        bad.write_text("---\nnot_a_real_key: hello\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch("sys.argv", ["dayamlchecker", "--show-experimental", str(bad)]):
                main()
        output = buf.getvalue()
        assert "[E301]" in output
        assert "REAL ERROR" in output


def test_cli_no_show_experimental_flag_via_main():
    """--no-show-experimental explicitly suppresses the REAL ERROR prefix."""
    with TemporaryDirectory() as tmp:
        bad = Path(tmp) / "bad.yml"
        bad.write_text("---\nnot_a_real_key: hello\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch(
                "sys.argv", ["dayamlchecker", "--no-show-experimental", str(bad)]
            ):
                main()
        output = buf.getvalue()
        assert "[E301]" in output
        assert "REAL ERROR" not in output


def test_package_main_aliases_yaml_structure_main():
    """The package entrypoint should directly expose the checker CLI main."""
    assert package_main is main
