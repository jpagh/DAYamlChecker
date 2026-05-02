"""Shared file-collection utilities used by both the formatter and the checker."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import tomllib


@dataclass(frozen=True)
class DayamlProjectConfig:
    project_root: Path
    yaml_path: Path
    ignore_codes: frozenset[str]
    cli_args: tuple[str, ...]


def _normalize_ignore_codes(raw_codes: object) -> frozenset[str]:
    if isinstance(raw_codes, str):
        values = raw_codes.split(",")
    elif isinstance(raw_codes, (list, tuple)):
        values = []
        for item in raw_codes:
            if isinstance(item, str):
                values.extend(item.split(","))
    else:
        return frozenset()
    return frozenset(code.strip().upper() for code in values if code.strip())


def _normalize_cli_args(raw_args: object) -> tuple[str, ...]:
    if isinstance(raw_args, str):
        return tuple(shlex.split(raw_args))
    if isinstance(raw_args, (list, tuple)):
        return tuple(item for item in raw_args if isinstance(item, str))
    return ()


def _load_dayaml_project_config(project_dir: Path) -> DayamlProjectConfig | None:
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.is_file():
        return None

    with pyproject_path.open("rb") as stream:
        pyproject = tomllib.load(stream)

    tool_section = pyproject.get("tool")
    dayaml_section = (
        tool_section.get("dayaml", {}) if isinstance(tool_section, dict) else {}
    )
    if not isinstance(dayaml_section, dict):
        dayaml_section = {}

    yaml_path_value = dayaml_section.get("yaml_path", "docassemble")
    yaml_path = Path("docassemble")
    if isinstance(yaml_path_value, str) and yaml_path_value.strip():
        yaml_path = Path(yaml_path_value)
    if not yaml_path.is_absolute():
        yaml_path = project_dir / yaml_path

    return DayamlProjectConfig(
        project_root=project_dir,
        yaml_path=yaml_path,
        ignore_codes=_normalize_ignore_codes(dayaml_section.get("ignore_codes", ())),
        cli_args=(
            _normalize_cli_args(dayaml_section.get("args", ()))
            + _normalize_cli_args(dayaml_section.get("check_args", ()))
        ),
    )


def _find_nearest_pyproject_dir(path: Path) -> Path | None:
    candidate = path if path.is_dir() else path.parent
    for directory in (candidate, *candidate.parents):
        if (directory / "pyproject.toml").is_file():
            return directory
    return None


def _collect_dayaml_ignore_codes(paths: list[Path]) -> frozenset[str]:
    ignore_codes: set[str] = set()
    seen_projects: set[Path] = set()

    for path in paths:
        project_dir = _find_nearest_pyproject_dir(path.resolve())
        if project_dir is None:
            continue
        project_dir = project_dir.resolve()
        if project_dir in seen_projects:
            continue
        seen_projects.add(project_dir)
        project_config = _load_dayaml_project_config(project_dir)
        if project_config is not None:
            ignore_codes.update(project_config.ignore_codes)

    return frozenset(ignore_codes)


def _collect_dayaml_cli_args(paths: list[Path]) -> tuple[str, ...]:
    cli_args: list[str] = []
    seen_projects: set[Path] = set()

    for path in paths:
        project_dir = _find_nearest_pyproject_dir(path.resolve())
        if project_dir is None:
            continue
        project_dir = project_dir.resolve()
        if project_dir in seen_projects:
            continue
        seen_projects.add(project_dir)
        project_config = _load_dayaml_project_config(project_dir)
        if project_config is not None:
            cli_args.extend(project_config.cli_args)

    return tuple(cli_args)


def _resolve_collection_path(path: Path) -> Path:
    if not path.is_dir():
        return path

    project_config = _load_dayaml_project_config(path.resolve())
    if project_config is None:
        return path
    return project_config.yaml_path


def _is_default_ignored_dir(dirname: str) -> bool:
    """Return True for directory names that should be skipped by default."""
    return (
        dirname.startswith(".git")
        or dirname.startswith(".github")
        or dirname.startswith(".venv")
        or dirname == "build"
        or dirname == "dist"
        or dirname == "node_modules"
        or dirname == "sources"
    )


def _collect_yaml_files(
    paths: list[Path],
    check_all: bool = False,
    include_default_ignores: bool | None = None,
) -> list[Path]:
    """Expand paths to a de-duplicated, sorted list of YAML files.

    - Files are included if they have .yml or .yaml extension
    - Directories are recursively searched for YAML files
    """
    if include_default_ignores is None:
        include_default_ignores = not check_all

    yaml_files: list[Path] = []
    for path in paths:
        path = _resolve_collection_path(path)
        if path.is_dir():
            # Recursively find all YAML files, pruning ignored directories
            for root, dirnames, filenames in os.walk(path, topdown=True):
                root_path = Path(root)
                if include_default_ignores:
                    if _is_default_ignored_dir(root_path.name):
                        dirnames[:] = []
                        continue
                    dirnames[:] = [
                        d for d in dirnames if not _is_default_ignored_dir(d)
                    ]
                for filename in filenames:
                    if filename.lower().endswith((".yml", ".yaml")):
                        yaml_files.append(root_path / filename)
        elif path.suffix.lower() in (".yml", ".yaml"):
            yaml_files.append(path)
    seen = set()
    result = []
    for f in yaml_files:
        resolved = f.resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(f)
    return sorted(result)
