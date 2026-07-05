from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.create_content_package import (
    PACKAGE_FILES,
    build_content_package,
    day_path_for_date,
    main,
    write_content_package,
)
from scripts.create_metadata import build_default_metadata, write_metadata_file


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


def test_build_content_package_returns_all_expected_files() -> None:
    files = build_content_package(_sample_metadata())

    assert set(files) == set(PACKAGE_FILES)


def test_build_content_package_uses_metadata_values() -> None:
    files = build_content_package(_sample_metadata())

    assert "Strong finish on tired legs" in files["exports/youtube/title.md"]
    assert (
        "Showing up on a low-energy morning still pays off."
        in files["exports/facebook/post.md"]
    )
    assert "the last 5 km changed everything" in files["exports/instagram/caption.md"]
    assert "the last 5 km changed everything" in files["exports/tiktok/hook.md"]
    assert "18.2 km" in files["exports/shorts/hook.md"]
    assert "HR 146 bpm" in files["exports/shorts/hook.md"]
    assert "kilometre 12" in files["thumbnails/ideas.md"]


def test_build_content_package_uses_placeholders_for_missing_fields() -> None:
    files = build_content_package(build_default_metadata(date(2026, 7, 5)))

    joined = "\n".join(files.values())
    assert "TODO" in joined


def test_write_content_package_creates_files_under_day_path(tmp_path: Path) -> None:
    files = build_content_package(_sample_metadata())
    day_path = day_path_for_date(date(2026, 7, 5), root=tmp_path)

    written = write_content_package(day_path, files)

    assert len(written) == len(PACKAGE_FILES)
    for relative in PACKAGE_FILES:
        assert (day_path / relative).exists()


def test_write_content_package_refuses_to_overwrite_without_flag(tmp_path: Path) -> None:
    files = build_content_package(_sample_metadata())
    day_path = day_path_for_date(date(2026, 7, 5), root=tmp_path)
    write_content_package(day_path, files)

    with pytest.raises(FileExistsError):
        write_content_package(day_path, files)


def test_write_content_package_can_overwrite_with_flag(tmp_path: Path) -> None:
    files = build_content_package(_sample_metadata())
    day_path = day_path_for_date(date(2026, 7, 5), root=tmp_path)
    write_content_package(day_path, files)

    # Should not raise.
    written = write_content_package(day_path, files, overwrite=True)

    assert len(written) == len(PACKAGE_FILES)


def test_main_creates_content_package_from_metadata(tmp_path: Path) -> None:
    day_path = day_path_for_date(date(2026, 7, 5), root=tmp_path)
    run_json = day_path / "metadata" / "run.json"
    write_metadata_file(run_json, _sample_metadata())

    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 0
    for relative in PACKAGE_FILES:
        assert (day_path / relative).exists()
    assert "Strong finish on tired legs" in (
        day_path / "exports" / "youtube" / "title.md"
    ).read_text(encoding="utf-8")


def test_main_fails_when_metadata_missing(tmp_path: Path) -> None:
    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 1


def test_main_dry_run_does_not_write_files(tmp_path: Path) -> None:
    day_path = day_path_for_date(date(2026, 7, 5), root=tmp_path)
    run_json = day_path / "metadata" / "run.json"
    write_metadata_file(run_json, _sample_metadata())

    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path), "--dry-run"])

    assert exit_code == 0
    for relative in PACKAGE_FILES:
        assert not (day_path / relative).exists()


def test_main_rejects_invalid_metadata(tmp_path: Path) -> None:
    day_path = day_path_for_date(date(2026, 7, 5), root=tmp_path)
    run_json = day_path / "metadata" / "run.json"
    metadata = _sample_metadata()
    write_metadata_file(run_json, metadata)

    # Corrupt the file on disk so validation fails when reloaded.
    metadata["privacy_level"] = "top_secret"
    import json

    run_json.write_text(json.dumps(metadata), encoding="utf-8")

    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 1
