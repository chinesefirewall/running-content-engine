from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.apple_health import AppleHealthImportError, parse_apple_health_export

SAMPLE_EXPORT = """<?xml version="1.0" encoding="UTF-8"?>
<HealthData locale="en_US">
  <ExportDate value="2026-07-05 09:00:00 -0400"/>
  <Record type="HKQuantityTypeIdentifierHeartRateVariabilitySDNN" sourceName="Watch" unit="ms" startDate="2026-07-05 06:00:00 -0400" endDate="2026-07-05 06:00:00 -0400" value="45.0"/>
  <Record type="HKQuantityTypeIdentifierHeartRateVariabilitySDNN" sourceName="Watch" unit="ms" startDate="2026-07-05 06:05:00 -0400" endDate="2026-07-05 06:05:00 -0400" value="47.0"/>
  <Record type="HKQuantityTypeIdentifierRestingHeartRate" sourceName="Watch" unit="count/min" startDate="2026-07-05 00:00:00 -0400" endDate="2026-07-05 00:00:00 -0400" value="52"/>
  <Record type="HKQuantityTypeIdentifierVO2Max" sourceName="Watch" unit="ml/min/kg" startDate="2026-07-04 08:00:00 -0400" endDate="2026-07-04 08:00:00 -0400" value="48.5"/>
  <Record type="HKCategoryTypeIdentifierSleepAnalysis" sourceName="Watch" startDate="2026-07-04 23:00:00 -0400" endDate="2026-07-05 06:00:00 -0400" value="HKCategoryValueSleepAnalysisAsleepCore"/>
  <Record type="HKCategoryTypeIdentifierSleepAnalysis" sourceName="Watch" startDate="2026-07-04 20:00:00 -0400" endDate="2026-07-04 21:00:00 -0400" value="HKCategoryValueSleepAnalysisInBed"/>
  <Workout workoutActivityType="HKWorkoutActivityTypeRunning" duration="52.0" durationUnit="min" totalDistance="10.0" totalDistanceUnit="km" totalEnergyBurned="620" totalEnergyBurnedUnit="kcal" sourceName="Watch" startDate="2026-07-05 06:10:00 -0400" endDate="2026-07-05 07:02:00 -0400"/>
  <Workout workoutActivityType="HKWorkoutActivityTypeCycling" duration="30.0" durationUnit="min" totalDistance="15.0" totalDistanceUnit="km" sourceName="Watch" startDate="2026-07-03 06:00:00 -0400" endDate="2026-07-03 06:30:00 -0400"/>
</HealthData>
"""


def _write_export(tmp_path: Path) -> Path:
    path = tmp_path / "export.xml"
    path.write_text(SAMPLE_EXPORT, encoding="utf-8")
    return path


def test_parse_apple_health_export_extracts_health_signals(tmp_path: Path) -> None:
    path = _write_export(tmp_path)

    summary = parse_apple_health_export(path, date(2026, 7, 5))

    assert summary.hrv_ms == pytest.approx(46.0)
    assert summary.resting_heart_rate == 52
    assert summary.sleep_hours == pytest.approx(7.0)
    # VO2 max was recorded the day before the target date, so it is not
    # attributed to this day.
    assert summary.vo2_max is None


def test_parse_apple_health_export_excludes_in_bed_from_sleep_hours(
    tmp_path: Path,
) -> None:
    path = _write_export(tmp_path)

    summary = parse_apple_health_export(path, date(2026, 7, 5))

    # Only the 7-hour "AsleepCore" interval counts; the 1-hour "InBed"
    # interval the evening before must not be added to it.
    assert summary.sleep_hours == pytest.approx(7.0)


def test_parse_apple_health_export_matches_same_day_running_workout(
    tmp_path: Path,
) -> None:
    path = _write_export(tmp_path)

    summary = parse_apple_health_export(path, date(2026, 7, 5))

    assert summary.workout_metrics is not None
    assert summary.workout_metrics["distance_km"] == pytest.approx(10.0)
    assert summary.workout_metrics["duration"] == "00:52:00"
    assert summary.workout_metrics["average_pace"] == "5:12/km"
    assert summary.workout_metrics["calories"] == 620
    assert summary.workout_metrics["source"] == "apple_health"


def test_parse_apple_health_export_ignores_non_running_workout(tmp_path: Path) -> None:
    path = _write_export(tmp_path)

    summary = parse_apple_health_export(path, date(2026, 7, 3))

    # Only a cycling workout exists on 2026-07-03 -- must not be reported as
    # a matched running workout.
    assert summary.workout_metrics is None


def test_parse_apple_health_export_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(AppleHealthImportError):
        parse_apple_health_export(tmp_path / "missing.xml", date(2026, 7, 5))


def test_parse_apple_health_export_invalid_xml_raises(tmp_path: Path) -> None:
    path = tmp_path / "export.xml"
    path.write_text("not xml at all <<<", encoding="utf-8")

    with pytest.raises(AppleHealthImportError):
        parse_apple_health_export(path, date(2026, 7, 5))
