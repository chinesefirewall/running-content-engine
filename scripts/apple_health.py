"""Parse a local Apple Health export into a health summary for one day.

Apple Health's manual "Export All Health Data" (Health app -> profile picture
-> Export All Health Data) produces ``export.zip`` containing ``export.xml``.
This is the same local-file, no-OAuth, no-API-key pattern as the existing
Garmin/Strava importers in ``scripts/import_activity.py``.

Unlike a single-activity TCX/GPX export, ``export.xml`` is a full multi-year
history dump that can be hundreds of megabytes. It is parsed with
``xml.etree.ElementTree.iterparse`` and each element is cleared immediately
after use, so memory stays bounded regardless of export size (``ET.parse``,
used for the small TCX/GPX exports, would load the whole file into memory).

Only aggregate values for the requested day (and, for sleep, the night
before it) are ever returned. No raw GPS or minute-by-minute health samples
are retained, matching Decision 004 (privacy-first).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

# HKQuantityTypeIdentifier record types this parser understands, mapped to
# the HealthSummary field they populate.
_RECORD_FIELD_MAP: dict[str, str] = {
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": "hrv_ms",
    "HKQuantityTypeIdentifierRestingHeartRate": "resting_heart_rate",
    "HKQuantityTypeIdentifierVO2Max": "vo2_max",
}
_SLEEP_RECORD_TYPE = "HKCategoryTypeIdentifierSleepAnalysis"
_RUNNING_WORKOUT_TYPES = {"HKWorkoutActivityTypeRunning"}


class AppleHealthImportError(Exception):
    """Raised when an Apple Health export cannot be parsed."""


@dataclass(frozen=True)
class HealthSummary:
    """Aggregate health signals for one day, plus an optional matched workout.

    ``workout_metrics``, when present, is shaped exactly like
    ``import_activity.ActivitySummary.as_metrics()`` (a plain dict with keys
    such as ``distance_km``, ``duration``, ``average_pace``, ``calories``,
    ``source``) so it can be merged with the same helper as the other
    importers.
    """

    hrv_ms: float | None = None
    resting_heart_rate: int | None = None
    sleep_hours: float | None = None
    vo2_max: float | None = None
    workout_metrics: dict[str, Any] | None = None


def _parse_apple_datetime(text: str | None) -> datetime | None:
    """Parse Apple Health's ``YYYY-MM-DD HH:MM:SS +ZZZZ`` timestamp.

    The trailing UTC offset is intentionally ignored: Apple Health always
    records the local wall-clock time alongside its offset, and wall-clock
    time is exactly what day-bucketing (matching records to a run date)
    needs.
    """

    if not text:
        return None
    parts = text.strip().split()
    if len(parts) < 2:
        return None
    try:
        return datetime.strptime(f"{parts[0]} {parts[1]}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _float_or_none(text: str | None) -> float | None:
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _convert_distance_km(value: float, unit: str | None) -> float:
    unit = (unit or "km").strip().lower()
    if unit in ("mi", "mile", "miles"):
        return value * 1.609344
    if unit in ("m", "meter", "meters"):
        return value / 1000
    return value


def _convert_duration_seconds(value: float, unit: str | None) -> float:
    unit = (unit or "min").strip().lower()
    if unit in ("sec", "second", "seconds", "s"):
        return value
    if unit in ("hr", "hour", "hours"):
        return value * 3600
    return value * 60


def _format_duration(total_seconds: float) -> str:
    seconds = int(round(total_seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _workout_metrics(elem: ET.Element) -> dict[str, Any]:
    """Build an ActivitySummary-shaped dict from a running <Workout> element."""

    metrics: dict[str, Any] = {"source": "apple_health"}

    distance = _float_or_none(elem.get("totalDistance"))
    distance_km = (
        round(_convert_distance_km(distance, elem.get("totalDistanceUnit")), 2)
        if distance is not None
        else None
    )
    if distance_km is not None:
        metrics["distance_km"] = distance_km

    duration = _float_or_none(elem.get("duration"))
    duration_seconds = (
        _convert_duration_seconds(duration, elem.get("durationUnit"))
        if duration is not None
        else None
    )
    if duration_seconds is not None:
        metrics["duration"] = _format_duration(duration_seconds)

    if distance_km and duration_seconds:
        pace_seconds = duration_seconds / distance_km
        minutes, seconds = divmod(int(round(pace_seconds)), 60)
        metrics["average_pace"] = f"{minutes}:{seconds:02d}/km"

    calories = _float_or_none(elem.get("totalEnergyBurned"))
    if calories is not None:
        metrics["calories"] = int(round(calories))

    return metrics


def parse_apple_health_export(path: Path, target_date: date) -> HealthSummary:
    """Stream-parse an Apple Health ``export.xml`` for one day's health data.

    Raises:
        AppleHealthImportError: if the file is missing or not valid XML.
    """

    if not path.exists():
        raise AppleHealthImportError(f"Apple Health export not found: {path}")

    # Sleep is bucketed to the night ending on the run day: noon the day
    # before through noon of the run day, which covers any bedtime.
    window_start = datetime.combine(target_date - timedelta(days=1), time(12, 0))
    window_end = datetime.combine(target_date, time(12, 0))

    hrv_values: list[float] = []
    resting_hr_values: list[float] = []
    vo2_values: list[float] = []
    sleep_seconds = 0.0
    workout_metrics: dict[str, Any] | None = None

    try:
        for _, elem in ET.iterparse(str(path), events=("end",)):
            if elem.tag == "Record":
                record_type = elem.get("type")
                if record_type in _RECORD_FIELD_MAP:
                    start = _parse_apple_datetime(elem.get("startDate"))
                    value = _float_or_none(elem.get("value"))
                    if start is not None and value is not None and start.date() == target_date:
                        field = _RECORD_FIELD_MAP[record_type]
                        if field == "hrv_ms":
                            hrv_values.append(value)
                        elif field == "resting_heart_rate":
                            resting_hr_values.append(value)
                        elif field == "vo2_max":
                            vo2_values.append(value)
                elif record_type == _SLEEP_RECORD_TYPE:
                    category_value = (elem.get("value") or "").lower()
                    if "asleep" in category_value:
                        start = _parse_apple_datetime(elem.get("startDate"))
                        end = _parse_apple_datetime(elem.get("endDate"))
                        if start is not None and end is not None:
                            overlap_start = max(start, window_start)
                            overlap_end = min(end, window_end)
                            if overlap_end > overlap_start:
                                sleep_seconds += (overlap_end - overlap_start).total_seconds()
            elif elem.tag == "Workout" and workout_metrics is None:
                if elem.get("workoutActivityType") in _RUNNING_WORKOUT_TYPES:
                    start = _parse_apple_datetime(elem.get("startDate"))
                    if start is not None and start.date() == target_date:
                        workout_metrics = _workout_metrics(elem)
            # Bounds memory on a multi-year, multi-hundred-MB export: each
            # element is dropped once its data has been extracted.
            elem.clear()
    except ET.ParseError as exc:
        raise AppleHealthImportError(f"Could not parse Apple Health export {path}: {exc}") from exc

    return HealthSummary(
        hrv_ms=round(sum(hrv_values) / len(hrv_values), 1) if hrv_values else None,
        resting_heart_rate=(
            int(round(sum(resting_hr_values) / len(resting_hr_values)))
            if resting_hr_values
            else None
        ),
        sleep_hours=round(sleep_seconds / 3600, 1) if sleep_seconds else None,
        vo2_max=round(sum(vo2_values) / len(vo2_values), 1) if vo2_values else None,
        workout_metrics=workout_metrics,
    )
