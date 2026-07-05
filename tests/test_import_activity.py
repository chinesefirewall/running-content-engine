from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pytest

from scripts.create_metadata import build_default_metadata, write_metadata_file
from scripts.import_activity import (
    ActivityImportError,
    ActivitySummary,
    apply_enrichment,
    detect_format,
    load_weather_json,
    main,
    merge_summary,
    parse_activity_json,
    parse_gpx,
    parse_strava_csv,
    parse_tcx,
    resolve_shoe,
)


def _metadata_path(tmp_path: Path, activity_date: date = date(2026, 7, 5)) -> Path:
    return (
        tmp_path
        / str(activity_date.year)
        / activity_date.isoformat()
        / "metadata"
        / "run.json"
    )

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"

# Keys that must never appear in any parsed output (privacy guarantee).
_FORBIDDEN_KEYS = {"lat", "lon", "latitude", "longitude", "position", "track", "points"}


def _assert_no_gps(summary: ActivitySummary) -> None:
    keys = {key.lower() for key in asdict(summary)}
    assert keys.isdisjoint(_FORBIDDEN_KEYS)


def test_parse_tcx_returns_expected_aggregates() -> None:
    summary = parse_tcx(SAMPLE_DIR / "garmin-activity.tcx")

    assert summary.distance_km == 10.0
    assert summary.duration == "00:52:00"
    assert summary.average_pace == "5:12/km"
    assert summary.average_heart_rate == 146
    assert summary.max_heart_rate == 172
    assert summary.elevation_gain_m == 13.0
    assert summary.calories == 620
    assert summary.source == "garmin"
    _assert_no_gps(summary)


def test_parse_gpx_computes_distance_and_discards_points() -> None:
    summary = parse_gpx(SAMPLE_DIR / "activity.gpx")

    assert summary.distance_km == pytest.approx(3.34, abs=0.05)
    assert summary.duration == "00:20:00"
    assert summary.average_heart_rate == 152
    assert summary.max_heart_rate == 170
    assert summary.elevation_gain_m == 11.0
    # GPX has no calories field.
    assert summary.calories is None
    _assert_no_gps(summary)


def test_parse_strava_csv_selects_row_by_date() -> None:
    summary = parse_strava_csv(SAMPLE_DIR / "strava-activities.csv", date(2026, 7, 5))

    assert summary.distance_km == 8.5
    assert summary.duration == "00:45:00"
    assert summary.average_heart_rate == 142
    assert summary.max_heart_rate == 168
    assert summary.elevation_gain_m == 55.0
    assert summary.calories == 540
    assert summary.source == "strava"
    _assert_no_gps(summary)


def test_parse_strava_csv_matches_the_other_date() -> None:
    summary = parse_strava_csv(SAMPLE_DIR / "strava-activities.csv", date(2026, 7, 6))

    assert summary.distance_km == 5.0
    assert summary.max_heart_rate == 150


def test_parse_strava_csv_missing_date_errors() -> None:
    with pytest.raises(ActivityImportError):
        parse_strava_csv(SAMPLE_DIR / "strava-activities.csv", date(2026, 1, 1))


def test_parse_strava_csv_requires_date_when_ambiguous() -> None:
    with pytest.raises(ActivityImportError):
        parse_strava_csv(SAMPLE_DIR / "strava-activities.csv")


def test_parse_activity_json_returns_expected_aggregates() -> None:
    summary = parse_activity_json(SAMPLE_DIR / "activity.json")

    assert summary.distance_km == 12.0
    assert summary.duration == "01:06:00"
    assert summary.average_pace == "5:30/km"
    assert summary.average_heart_rate == 148
    assert summary.max_heart_rate == 176
    assert summary.elevation_gain_m == 84.0
    assert summary.calories == 710
    assert summary.source == "strava"
    _assert_no_gps(summary)


def test_parse_activity_json_accepts_distance_in_meters(tmp_path: Path) -> None:
    payload = {"distance_meters": 5000, "duration_seconds": 1500}
    path = tmp_path / "activity.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    summary = parse_activity_json(path, source="garmin")

    assert summary.distance_km == 5.0
    assert summary.duration == "00:25:00"
    assert summary.source == "garmin"


def test_parse_missing_metrics_stay_none(tmp_path: Path) -> None:
    path = tmp_path / "activity.json"
    path.write_text(json.dumps({"distance_km": 4.0}), encoding="utf-8")

    summary = parse_activity_json(path)

    # No duration -> no derived pace, and unrelated metrics remain None.
    assert summary.average_pace is None
    assert summary.average_heart_rate is None
    assert summary.calories is None


def test_parse_activity_json_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ActivityImportError):
        parse_activity_json(path)


def test_as_metrics_only_includes_set_fields() -> None:
    summary = ActivitySummary(distance_km=5.0, source="garmin")

    metrics = summary.as_metrics()

    assert metrics == {"distance_km": 5.0, "source": "garmin"}


def test_detect_format_by_extension(tmp_path: Path) -> None:
    assert detect_format(SAMPLE_DIR / "garmin-activity.tcx") == "tcx"
    assert detect_format(SAMPLE_DIR / "activity.gpx") == "gpx"
    assert detect_format(SAMPLE_DIR / "strava-activities.csv") == "csv"
    assert detect_format(SAMPLE_DIR / "activity.json") == "json"


def test_detect_format_by_content(tmp_path: Path) -> None:
    gpx = tmp_path / "export.dat"
    gpx.write_text('<?xml version="1.0"?><gpx></gpx>', encoding="utf-8")
    assert detect_format(gpx) == "gpx"


def test_detect_format_unknown_raises(tmp_path: Path) -> None:
    unknown = tmp_path / "export.dat"
    unknown.write_text("just some prose", encoding="utf-8")
    with pytest.raises(ActivityImportError):
        detect_format(unknown)


def test_merge_summary_fills_only_provided_fields() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    summary = ActivitySummary(distance_km=10.0, duration="00:52:00", source="garmin")

    merge_summary(metadata, summary)

    assert metadata["metrics"]["distance_km"] == 10.0
    assert metadata["metrics"]["duration"] == "00:52:00"
    # Unprovided metric stays None.
    assert metadata["metrics"]["calories"] is None
    # Source upgrades from the default "manual".
    assert metadata["metrics"]["source"] == "garmin"


def test_merge_summary_preserves_existing_without_overwrite() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["metrics"]["distance_km"] = 5.0
    summary = ActivitySummary(distance_km=10.0)

    merge_summary(metadata, summary)

    assert metadata["metrics"]["distance_km"] == 5.0


def test_merge_summary_overwrites_with_flag() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["metrics"]["distance_km"] = 5.0
    summary = ActivitySummary(distance_km=10.0)

    merge_summary(metadata, summary, overwrite=True)

    assert metadata["metrics"]["distance_km"] == 10.0


def test_main_creates_metadata_when_missing(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--file",
            str(SAMPLE_DIR / "garmin-activity.tcx"),
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    path = _metadata_path(tmp_path)
    assert path.exists()
    metadata = json.loads(path.read_text(encoding="utf-8"))
    assert metadata["metrics"]["distance_km"] == 10.0
    assert metadata["metrics"]["source"] == "garmin"


def test_main_merges_into_existing_and_preserves_fields(tmp_path: Path) -> None:
    path = _metadata_path(tmp_path)
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["content_notes"]["mood"] = "felt great"
    metadata["gear"]["shoes"] = "Sample Trainer 5"
    write_metadata_file(path, metadata)

    exit_code = main(
        [
            "--file",
            str(SAMPLE_DIR / "activity.json"),
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    updated = json.loads(path.read_text(encoding="utf-8"))
    assert updated["metrics"]["distance_km"] == 12.0
    # Unrelated fields are preserved.
    assert updated["content_notes"]["mood"] == "felt great"
    assert updated["gear"]["shoes"] == "Sample Trainer 5"


def test_main_source_override(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--file",
            str(SAMPLE_DIR / "garmin-activity.tcx"),
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
            "--source",
            "other",
        ]
    )

    assert exit_code == 0
    metadata = json.loads(_metadata_path(tmp_path).read_text(encoding="utf-8"))
    assert metadata["metrics"]["source"] == "other"


def test_main_dry_run_writes_nothing(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--file",
            str(SAMPLE_DIR / "garmin-activity.tcx"),
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert not _metadata_path(tmp_path).exists()


def test_main_unknown_file_errors(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--file",
            str(tmp_path / "missing.tcx"),
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
        ]
    )

    assert exit_code == 1


def test_main_output_has_no_gps_keys(tmp_path: Path) -> None:
    main(
        [
            "--file",
            str(SAMPLE_DIR / "activity.gpx"),
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
        ]
    )

    raw = _metadata_path(tmp_path).read_text(encoding="utf-8").lower()
    for token in ("latitude", "longitude", "\"lat\"", "\"lon\"", "trackpoint"):
        assert token not in raw


def test_apply_enrichment_populates_conditions_and_gear() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))

    apply_enrichment(
        metadata,
        weather="clear",
        temperature_c=16.5,
        wind="calm",
        shoes="Sample Trainer 5",
        watch="Sample Watch 2",
    )

    assert metadata["conditions"]["weather"] == "clear"
    assert metadata["conditions"]["temperature_c"] == 16.5
    assert metadata["conditions"]["wind"] == "calm"
    assert metadata["gear"]["shoes"] == "Sample Trainer 5"
    assert metadata["gear"]["watch"] == "Sample Watch 2"


def test_apply_enrichment_preserves_existing_without_overwrite() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["gear"]["shoes"] = "Old Shoes"

    apply_enrichment(metadata, shoes="New Shoes")

    assert metadata["gear"]["shoes"] == "Old Shoes"


def test_apply_enrichment_overwrites_with_flag() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["gear"]["shoes"] = "Old Shoes"

    apply_enrichment(metadata, shoes="New Shoes", overwrite=True)

    assert metadata["gear"]["shoes"] == "New Shoes"


def test_load_weather_json(tmp_path: Path) -> None:
    path = tmp_path / "weather.json"
    path.write_text(
        json.dumps({"weather": "light rain", "temperature": 12, "wind": "breezy"}),
        encoding="utf-8",
    )

    values = load_weather_json(path)

    assert values == {
        "weather": "light rain",
        "temperature_c": 12.0,
        "wind": "breezy",
    }


def test_resolve_shoe_uses_registry(tmp_path: Path) -> None:
    registry = tmp_path / "shoes.json"
    registry.write_text(
        json.dumps({"daily": "Sample Trainer 5"}), encoding="utf-8"
    )

    assert resolve_shoe("daily", registry) == "Sample Trainer 5"
    # Unknown alias is returned unchanged.
    assert resolve_shoe("other", registry) == "other"
    # No registry means the original value passes through.
    assert resolve_shoe("daily", None) == "daily"


def test_main_enrichment_only_without_file(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
            "--weather",
            "clear",
            "--temperature-c",
            "16",
            "--shoes",
            "Sample Trainer 5",
        ]
    )

    assert exit_code == 0
    metadata = json.loads(_metadata_path(tmp_path).read_text(encoding="utf-8"))
    assert metadata["conditions"]["weather"] == "clear"
    assert metadata["conditions"]["temperature_c"] == 16.0
    assert metadata["gear"]["shoes"] == "Sample Trainer 5"


def test_main_requires_file_or_enrichment(tmp_path: Path) -> None:
    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 1


def test_main_combined_file_and_enrichment(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--file",
            str(SAMPLE_DIR / "garmin-activity.tcx"),
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
            "--weather",
            "clear",
            "--shoes",
            "Sample Trainer 5",
        ]
    )

    assert exit_code == 0
    metadata = json.loads(_metadata_path(tmp_path).read_text(encoding="utf-8"))
    assert metadata["metrics"]["distance_km"] == 10.0
    assert metadata["conditions"]["weather"] == "clear"
    assert metadata["gear"]["shoes"] == "Sample Trainer 5"


def test_main_weather_file_with_flag_override(tmp_path: Path) -> None:
    weather_file = tmp_path / "weather.json"
    weather_file.write_text(
        json.dumps({"weather": "cloudy", "temperature_c": 10, "wind": "calm"}),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
            "--weather-file",
            str(weather_file),
            "--weather",
            "sunny",
        ]
    )

    assert exit_code == 0
    metadata = json.loads(_metadata_path(tmp_path).read_text(encoding="utf-8"))
    # Flag overrides the file value; other file values still applied.
    assert metadata["conditions"]["weather"] == "sunny"
    assert metadata["conditions"]["temperature_c"] == 10.0
    assert metadata["conditions"]["wind"] == "calm"


def test_main_rejects_invalid_metadata_on_disk(tmp_path: Path) -> None:
    path = _metadata_path(tmp_path)
    metadata = build_default_metadata(date(2026, 7, 5))
    write_metadata_file(path, metadata)
    # Corrupt the file so validation fails when reloaded.
    metadata["privacy_level"] = "top_secret"
    path.write_text(json.dumps(metadata), encoding="utf-8")

    exit_code = main(
        [
            "--file",
            str(SAMPLE_DIR / "garmin-activity.tcx"),
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
        ]
    )

    assert exit_code == 1
