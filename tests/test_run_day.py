from __future__ import annotations

from datetime import date
from pathlib import Path

from scripts.create_content_package import PACKAGE_FILES, day_path_for_date
from scripts.create_metadata import metadata_path_for_date
from scripts.create_story_brief import story_brief_path_for_date
from scripts.run_day import build_parser, build_steps, main


def _args(argv: list[str]):
    return build_parser().parse_args(argv)


def test_build_steps_default_order(tmp_path: Path) -> None:
    args = _args(["--date", "2026-07-05", "--root", str(tmp_path)])

    steps = build_steps(args)

    assert [step.name for step in steps] == [
        "create_day",
        "create_metadata",
        "create_story_brief",
        "create_content_package",
    ]


def test_build_steps_inserts_import_when_requested(tmp_path: Path) -> None:
    args = _args(
        ["--date", "2026-07-05", "--root", str(tmp_path), "--shoes", "Sample Trainer 5"]
    )

    steps = build_steps(args)

    assert [step.name for step in steps] == [
        "create_day",
        "create_metadata",
        "import_activity",
        "create_story_brief",
        "create_content_package",
    ]


def test_main_runs_full_pipeline(tmp_path: Path) -> None:
    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 0

    day_path = day_path_for_date(date(2026, 7, 5), root=tmp_path)
    assert metadata_path_for_date(date(2026, 7, 5), root=tmp_path).exists()
    assert story_brief_path_for_date(date(2026, 7, 5), root=tmp_path).exists()
    for relative in PACKAGE_FILES:
        assert (day_path / relative).exists()


def test_main_is_idempotent(tmp_path: Path) -> None:
    first = main(["--date", "2026-07-05", "--root", str(tmp_path)])
    second = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert first == 0
    assert second == 0


def test_main_dry_run_creates_no_files(tmp_path: Path) -> None:
    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path), "--dry-run"])

    assert exit_code == 0
    assert not metadata_path_for_date(date(2026, 7, 5), root=tmp_path).exists()
    assert not day_path_for_date(date(2026, 7, 5), root=tmp_path).exists()
