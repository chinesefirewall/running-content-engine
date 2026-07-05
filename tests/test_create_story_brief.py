from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.create_metadata import build_default_metadata, write_metadata_file
from scripts.create_story_brief import (
    build_story_brief,
    main,
    read_notes,
    story_brief_path_for_date,
    write_story_brief,
)


def _sample_metadata() -> dict:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["title_working"] = "Strong finish on tired legs"
    metadata["metrics"].update(
        {
            "distance_km": 18.2,
            "duration": "01:44:00",
            "average_pace": "5:42/km",
            "average_heart_rate": 146,
        }
    )
    metadata["content_notes"].update(
        {
            "mood": "started tired, finished strong",
            "lesson": "Energy improved after the first few kilometres.",
            "story_angle": "Showing up on a low-energy morning still pays off.",
            "hook": "I did not feel ready, but the last 5 km changed everything.",
            "key_moment": "The pace felt easier after kilometre 12.",
        }
    )
    return metadata


def test_build_story_brief_includes_all_platform_sections() -> None:
    brief = build_story_brief(_sample_metadata())

    for heading in (
        "## Daily story angle",
        "## YouTube title",
        "## Instagram caption",
        "## TikTok hook",
        "## Facebook post",
        "## Overlay text",
        "## Thumbnail ideas",
        "## Review checklist",
    ):
        assert heading in brief


def test_build_story_brief_uses_metadata_values() -> None:
    brief = build_story_brief(_sample_metadata())

    assert "Story Brief - 2026-07-05" in brief
    assert "Strong finish on tired legs" in brief
    assert "Showing up on a low-energy morning still pays off." in brief
    assert "the last 5 km changed everything" in brief
    assert "18.2 km" in brief
    assert "5:42/km" in brief
    assert "HR 146 bpm" in brief


def test_build_story_brief_uses_placeholders_for_missing_fields() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))

    brief = build_story_brief(metadata)

    assert "TODO" in brief
    assert "_No notes recorded for this day._" in brief


def test_build_story_brief_includes_notes_when_present() -> None:
    brief = build_story_brief(_sample_metadata(), notes="Felt the wind on the bridge.")

    assert "Felt the wind on the bridge." in brief
    assert "_No notes recorded for this day._" not in brief


def test_story_brief_path_for_date_uses_notes_folder(tmp_path: Path) -> None:
    path = story_brief_path_for_date(date(2026, 7, 5), root=tmp_path)

    assert path == (
        tmp_path.resolve() / "2026" / "2026-07-05" / "notes" / "story-brief.md"
    )


def test_read_notes_returns_none_when_no_notes(tmp_path: Path) -> None:
    assert read_notes(date(2026, 7, 5), root=tmp_path) is None


def test_read_notes_combines_notes_and_skips_story_brief(tmp_path: Path) -> None:
    notes_dir = tmp_path / "2026" / "2026-07-05" / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / "a-morning.md").write_text("Cold start.", encoding="utf-8")
    (notes_dir / "b-evening.md").write_text("Good recovery.", encoding="utf-8")
    (notes_dir / "story-brief.md").write_text("Should be ignored.", encoding="utf-8")

    notes = read_notes(date(2026, 7, 5), root=tmp_path)

    assert notes is not None
    assert "Cold start." in notes
    assert "Good recovery." in notes
    assert "Should be ignored." not in notes


def test_write_story_brief_refuses_to_overwrite_without_flag(tmp_path: Path) -> None:
    path = tmp_path / "story-brief.md"
    write_story_brief(path, "first")

    with pytest.raises(FileExistsError):
        write_story_brief(path, "second")


def test_write_story_brief_can_overwrite_with_flag(tmp_path: Path) -> None:
    path = tmp_path / "story-brief.md"
    write_story_brief(path, "first")
    write_story_brief(path, "second", overwrite=True)

    assert path.read_text(encoding="utf-8").strip() == "second"


def test_main_creates_story_brief_from_metadata(tmp_path: Path) -> None:
    metadata_path = story_brief_path_for_date(date(2026, 7, 5), root=tmp_path)
    run_json = metadata_path.parent.parent / "metadata" / "run.json"
    write_metadata_file(run_json, _sample_metadata())

    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 0
    brief_path = story_brief_path_for_date(date(2026, 7, 5), root=tmp_path)
    assert brief_path.exists()
    assert "Story Brief - 2026-07-05" in brief_path.read_text(encoding="utf-8")


def test_main_fails_when_metadata_missing(tmp_path: Path) -> None:
    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 1
