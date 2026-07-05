from __future__ import annotations

from datetime import date
from pathlib import Path

from scripts.create_day import build_workspace_plan, create_workspace, parse_activity_date


def test_parse_activity_date_accepts_iso_date() -> None:
    assert parse_activity_date("2026-07-05") == date(2026, 7, 5)


def test_build_workspace_plan_uses_year_and_date_folder(tmp_path: Path) -> None:
    plan = build_workspace_plan(activity_date=date(2026, 7, 5), root=tmp_path)

    assert plan.day_path == tmp_path.resolve() / "2026" / "2026-07-05"
    assert tmp_path.resolve() / "2026" / "2026-07-05" / "raw" in plan.directories
    assert tmp_path.resolve() / "2026" / "2026-07-05" / "exports" / "instagram" in plan.directories
    assert tmp_path.resolve() / "2026" / "2026-07-05" / "metadata" in plan.directories


def test_create_workspace_creates_expected_directories(tmp_path: Path) -> None:
    plan = build_workspace_plan(activity_date=date(2026, 7, 5), root=tmp_path)

    create_workspace(plan)

    for directory in plan.directories:
        assert directory.exists()
        assert directory.is_dir()


def test_create_workspace_dry_run_does_not_create_directories(tmp_path: Path) -> None:
    plan = build_workspace_plan(activity_date=date(2026, 7, 5), root=tmp_path)

    planned = create_workspace(plan, dry_run=True)

    assert planned == list(plan.directories)
    assert not plan.day_path.exists()
