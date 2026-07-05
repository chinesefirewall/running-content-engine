from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from scripts.create_metadata import (
    MetadataValidationError,
    build_default_metadata,
    load_schema,
    metadata_path_for_date,
    validate_metadata,
    write_metadata_file,
)


def test_build_default_metadata_has_required_top_level_fields() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))

    assert metadata["date"] == "2026-07-05"
    assert metadata["activity_type"] == "run"
    assert metadata["recording_type"] == "daily_run"
    assert metadata["privacy_level"] == "private"
    assert metadata["metrics"]["source"] == "manual"
    assert metadata["content_notes"]["publish_intent"] == "do_not_publish"
    assert metadata["clips"] == []


def test_metadata_path_for_date_uses_daily_workspace(tmp_path: Path) -> None:
    path = metadata_path_for_date(date(2026, 7, 5), root=tmp_path)

    assert path == tmp_path.resolve() / "2026" / "2026-07-05" / "metadata" / "run.json"


def test_write_metadata_file_creates_parent_directories(tmp_path: Path) -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    path = tmp_path / "2026" / "2026-07-05" / "metadata" / "run.json"

    write_metadata_file(path, metadata)

    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["date"] == "2026-07-05"


def test_write_metadata_file_refuses_to_overwrite_without_flag(tmp_path: Path) -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    path = tmp_path / "run.json"

    write_metadata_file(path, metadata)

    with pytest.raises(FileExistsError):
        write_metadata_file(path, metadata)


def test_write_metadata_file_can_overwrite_with_flag(tmp_path: Path) -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    path = tmp_path / "run.json"

    write_metadata_file(path, metadata)
    metadata["activity_type"] = "walk"
    write_metadata_file(path, metadata, overwrite=True)

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["activity_type"] == "walk"


def test_default_metadata_passes_schema_validation() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))

    # Should not raise.
    validate_metadata(metadata)


def test_bundled_sample_passes_schema_validation() -> None:
    sample_path = (
        Path(__file__).resolve().parent.parent
        / "examples"
        / "run_metadata.sample.json"
    )
    sample = json.loads(sample_path.read_text(encoding="utf-8"))

    validate_metadata(sample)


def test_validate_metadata_rejects_missing_required_field() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    del metadata["metrics"]

    with pytest.raises(MetadataValidationError):
        validate_metadata(metadata)


def test_validate_metadata_rejects_invalid_enum_value() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["privacy_level"] = "top_secret"

    with pytest.raises(MetadataValidationError):
        validate_metadata(metadata)


def test_validate_metadata_rejects_unknown_property() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["unexpected_field"] = "nope"

    with pytest.raises(MetadataValidationError):
        validate_metadata(metadata)


def test_write_metadata_file_rejects_invalid_metadata(tmp_path: Path) -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["privacy_level"] = "top_secret"
    path = tmp_path / "run.json"

    with pytest.raises(MetadataValidationError):
        write_metadata_file(path, metadata)

    assert not path.exists()


def test_load_schema_returns_expected_required_fields() -> None:
    schema = load_schema()

    assert "date" in schema["required"]
    assert "metrics" in schema["required"]
    assert "content_notes" in schema["required"]
