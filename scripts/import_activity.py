#!/usr/bin/env python3
"""Import summary metrics from a local Garmin/Strava export into run metadata.

This tool parses a local activity export (TCX, GPX, Strava CSV, or a generic
activity JSON) and merges only aggregate summary metrics into the day's
``content/YYYY/YYYY-MM-DD/metadata/run.json``. It never has to type run data by
hand, and it fits the same deterministic, local-first pattern as the other
scripts in this repository.

Privacy by construction (see docs/decision-log.md, Decision 004): GPS trackpoints
are read transiently only to compute aggregates (distance, elevation gain) and
are **never stored**. No latitude/longitude ever reaches ``run.json``. The tool
makes no network calls and never publishes anything.

Example:
    python scripts/import_activity.py --file data/sample/garmin-activity.tcx --date 2026-07-05
    python scripts/import_activity.py --file data/sample/activity.gpx --date today --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Allow running this file directly (e.g. `python scripts/import_activity.py`).
# When executed as a script, Python puts the `scripts/` directory on sys.path
# instead of the project root, which breaks the `scripts.` package import below.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.create_day import parse_activity_date
from scripts.create_metadata import (
    MetadataValidationError,
    build_default_metadata,
    metadata_path_for_date,
    validate_metadata,
    write_metadata_file,
)

# Fields the importer is allowed to populate from a parsed export.
SUMMARY_METRIC_FIELDS: tuple[str, ...] = (
    "distance_km",
    "duration",
    "average_pace",
    "average_heart_rate",
    "max_heart_rate",
    "elevation_gain_m",
    "calories",
)

VALID_SOURCES: tuple[str, ...] = ("manual", "garmin", "strava", "apple_health", "other")


class ActivityImportError(Exception):
    """Raised when an export cannot be parsed or matched."""


@dataclass(frozen=True)
class ActivitySummary:
    """Normalized, aggregate-only summary of one activity export.

    Only summary metrics are represented here; no GPS points are ever retained.
    """

    distance_km: float | None = None
    duration: str | None = None  # HH:MM:SS
    average_pace: str | None = None  # e.g. "5:42/km" (derived)
    average_heart_rate: int | None = None
    max_heart_rate: int | None = None
    elevation_gain_m: float | None = None
    calories: int | None = None
    source: str | None = None  # manual|garmin|strava|apple_health|other

    def as_metrics(self) -> dict[str, Any]:
        """Return the summary as a metrics-shaped dict (only set fields)."""

        values: dict[str, Any] = {}
        for field in SUMMARY_METRIC_FIELDS:
            value = getattr(self, field)
            if value is not None:
                values[field] = value
        if self.source is not None:
            values["source"] = self.source
        return values


# ---------------------------------------------------------------------------
# Shared numeric / formatting helpers
# ---------------------------------------------------------------------------


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""

    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * radius_km * math.asin(math.sqrt(a))


def _format_duration(total_seconds: float | None) -> str | None:
    """Format a number of seconds as HH:MM:SS."""

    if total_seconds is None or total_seconds <= 0:
        return None
    seconds = int(round(total_seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _derive_pace(distance_km: float | None, total_seconds: float | None) -> str | None:
    """Derive an average pace string (M:SS/km) from distance and duration."""

    if not distance_km or distance_km <= 0 or not total_seconds or total_seconds <= 0:
        return None
    pace_seconds = total_seconds / distance_km
    minutes, seconds = divmod(int(round(pace_seconds)), 60)
    return f"{minutes}:{seconds:02d}/km"


def _elevation_gain(altitudes: Iterable[float]) -> float | None:
    """Sum of positive altitude deltas (metres) over a sequence of samples."""

    gain = 0.0
    previous: float | None = None
    seen = False
    for altitude in altitudes:
        seen = True
        if previous is not None and altitude > previous:
            gain += altitude - previous
        previous = altitude
    return round(gain, 1) if seen else None


def _summary_from_raw(
    *,
    distance_km: float | None,
    duration_seconds: float | None,
    average_heart_rate: float | None,
    max_heart_rate: float | None,
    elevation_gain_m: float | None,
    calories: float | None,
    source: str | None,
) -> ActivitySummary:
    """Build an ActivitySummary from raw numeric aggregates.

    Duration is formatted as HH:MM:SS and pace is derived from distance and
    duration. Missing inputs stay ``None`` (values are never fabricated).
    """

    distance = round(distance_km, 2) if distance_km else None
    return ActivitySummary(
        distance_km=distance,
        duration=_format_duration(duration_seconds),
        average_pace=_derive_pace(distance, duration_seconds),
        average_heart_rate=int(round(average_heart_rate))
        if average_heart_rate
        else None,
        max_heart_rate=int(round(max_heart_rate)) if max_heart_rate else None,
        elevation_gain_m=elevation_gain_m,
        calories=int(round(calories)) if calories else None,
        source=source,
    )


# ---------------------------------------------------------------------------
# XML helpers (namespace-agnostic)
# ---------------------------------------------------------------------------


def _local_name(tag: str) -> str:
    """Return an XML tag's local name, stripping any namespace prefix."""

    return tag.rsplit("}", 1)[-1]


def _iter_local(element: ET.Element, name: str) -> Iterable[ET.Element]:
    """Yield descendant elements whose local name matches ``name``."""

    for child in element.iter():
        if _local_name(child.tag) == name:
            yield child


def _first_local(element: ET.Element, name: str) -> ET.Element | None:
    """Return the first descendant element with the given local name, or None."""

    for match in _iter_local(element, name):
        return match
    return None


def _float_or_none(text: str | None) -> float | None:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Parsers (stdlib only). Each returns an ActivitySummary of aggregates.
# ---------------------------------------------------------------------------


def parse_tcx(path: Path, source: str = "garmin") -> ActivitySummary:
    """Parse a Garmin/TCX export into an ActivitySummary.

    GPS positions are ignored; only aggregate metrics are computed.
    """

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ActivityImportError(f"Could not parse TCX file {path}: {exc}") from exc

    total_distance_m = 0.0
    total_seconds = 0.0
    total_calories = 0.0
    hr_avg_samples: list[tuple[float, float]] = []  # (value, weight)
    hr_max_values: list[float] = []

    for lap in _iter_local(root, "Lap"):
        distance = _float_or_none(_lap_text(lap, "DistanceMeters"))
        seconds = _float_or_none(_lap_text(lap, "TotalTimeSeconds"))
        calories = _float_or_none(_lap_text(lap, "Calories"))
        if distance:
            total_distance_m += distance
        if seconds:
            total_seconds += seconds
        if calories:
            total_calories += calories

        avg_hr_el = _first_local(lap, "AverageHeartRateBpm")
        if avg_hr_el is not None:
            avg_hr = _float_or_none(_first_value(avg_hr_el))
            if avg_hr:
                hr_avg_samples.append((avg_hr, seconds or 1.0))
        max_hr_el = _first_local(lap, "MaximumHeartRateBpm")
        if max_hr_el is not None:
            max_hr = _float_or_none(_first_value(max_hr_el))
            if max_hr:
                hr_max_values.append(max_hr)

    # Elevation gain from trackpoint altitudes (positions discarded).
    altitudes = [
        value
        for value in (
            _float_or_none(alt.text) for alt in _iter_local(root, "AltitudeMeters")
        )
        if value is not None
    ]

    average_hr = _weighted_average(hr_avg_samples)
    max_hr = max(hr_max_values) if hr_max_values else None

    return _summary_from_raw(
        distance_km=total_distance_m / 1000 if total_distance_m else None,
        duration_seconds=total_seconds or None,
        average_heart_rate=average_hr,
        max_heart_rate=max_hr,
        elevation_gain_m=_elevation_gain(altitudes),
        calories=total_calories or None,
        source=source,
    )


def _lap_text(lap: ET.Element, name: str) -> str | None:
    """Return the text of a direct-ish child of a lap by local name."""

    element = _first_local(lap, name)
    return element.text if element is not None else None


def _first_value(element: ET.Element) -> str | None:
    """Return the text of a nested <Value> element (TCX HR wrappers)."""

    value = _first_local(element, "Value")
    if value is not None:
        return value.text
    return element.text


def _weighted_average(samples: list[tuple[float, float]]) -> float | None:
    """Weighted average of (value, weight) pairs, or None if empty."""

    total_weight = sum(weight for _, weight in samples)
    if not samples or total_weight <= 0:
        return None
    return sum(value * weight for value, weight in samples) / total_weight


def parse_gpx(path: Path, source: str = "garmin") -> ActivitySummary:
    """Parse a GPX export into an ActivitySummary.

    Distance is computed via the haversine formula over consecutive trackpoints,
    which are then discarded: no latitude/longitude is retained.
    """

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ActivityImportError(f"Could not parse GPX file {path}: {exc}") from exc

    total_distance_km = 0.0
    previous_point: tuple[float, float] | None = None
    altitudes: list[float] = []
    times: list[datetime] = []
    hr_values: list[float] = []

    for point in _iter_local(root, "trkpt"):
        lat = _float_or_none(point.get("lat"))
        lon = _float_or_none(point.get("lon"))
        if lat is not None and lon is not None:
            if previous_point is not None:
                total_distance_km += _haversine_km(
                    previous_point[0], previous_point[1], lat, lon
                )
            previous_point = (lat, lon)

        ele = _first_local(point, "ele")
        altitude = _float_or_none(ele.text) if ele is not None else None
        if altitude is not None:
            altitudes.append(altitude)

        time_el = _first_local(point, "time")
        parsed_time = _parse_iso_datetime(time_el.text) if time_el is not None else None
        if parsed_time is not None:
            times.append(parsed_time)

        hr_el = _first_local(point, "hr")
        hr = _float_or_none(hr_el.text) if hr_el is not None else None
        if hr is not None:
            hr_values.append(hr)

    # Discard positional data explicitly once aggregates are computed.
    previous_point = None

    duration_seconds = None
    if len(times) >= 2:
        duration_seconds = (max(times) - min(times)).total_seconds()

    average_hr = sum(hr_values) / len(hr_values) if hr_values else None
    max_hr = max(hr_values) if hr_values else None

    return _summary_from_raw(
        distance_km=total_distance_km or None,
        duration_seconds=duration_seconds,
        average_heart_rate=average_hr,
        max_heart_rate=max_hr,
        elevation_gain_m=_elevation_gain(altitudes),
        calories=None,
        source=source,
    )


def _parse_iso_datetime(text: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp (with optional trailing Z)."""

    if not text:
        return None
    normalized = text.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def parse_strava_csv(
    path: Path, activity_date: date | None = None, source: str = "strava"
) -> ActivitySummary:
    """Parse a Strava activities CSV export into an ActivitySummary.

    When multiple activities are present, ``activity_date`` selects the matching
    row. An ambiguous or missing match raises ``ActivityImportError``.
    """

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ActivityImportError(f"Strava CSV has no rows: {path}")

    if activity_date is not None:
        matching = [row for row in rows if _row_matches_date(row, activity_date)]
        if not matching:
            raise ActivityImportError(
                f"No Strava activity found for {activity_date.isoformat()} in {path}."
            )
        if len(matching) > 1:
            raise ActivityImportError(
                f"Multiple Strava activities found for {activity_date.isoformat()} "
                f"in {path}. Cannot choose one unambiguously."
            )
        row = matching[0]
    elif len(rows) == 1:
        row = rows[0]
    else:
        raise ActivityImportError(
            f"Strava CSV {path} has multiple rows; pass --date to select one."
        )

    distance_km = _row_number(row, ("distance",))
    duration_seconds = _row_number(row, ("moving time", "elapsed time"))
    average_hr = _row_number(row, ("average heart rate",))
    max_hr = _row_number(row, ("max heart rate",))
    elevation = _row_number(row, ("elevation gain",))
    calories = _row_number(row, ("calories",))

    return _summary_from_raw(
        distance_km=distance_km,
        duration_seconds=duration_seconds,
        average_heart_rate=average_hr,
        max_heart_rate=max_hr,
        elevation_gain_m=round(elevation, 1) if elevation else None,
        calories=calories,
        source=source,
    )


def _row_get(row: dict[str, str], keyword: str) -> str | None:
    """Return a CSV cell whose header contains ``keyword`` (case-insensitive)."""

    keyword = keyword.lower()
    for header, value in row.items():
        if header and keyword in header.lower():
            return value
    return None


def _row_number(row: dict[str, str], keywords: tuple[str, ...]) -> float | None:
    """Return the first parseable numeric cell matching any keyword."""

    for keyword in keywords:
        value = _row_get(row, keyword)
        number = _float_or_none(value)
        if number is not None:
            return number
    return None


def _row_matches_date(row: dict[str, str], activity_date: date) -> bool:
    """Return True if a Strava row's activity date matches ``activity_date``."""

    raw = _row_get(row, "date")
    parsed = _parse_activity_datetime(raw)
    return parsed is not None and parsed == activity_date


def _parse_activity_datetime(text: str | None) -> date | None:
    """Parse a Strava activity date cell into a ``date``.

    Handles Strava's human-readable export format as well as ISO-like values.
    """

    if not text:
        return None
    text = text.strip()

    iso = _parse_iso_datetime(text)
    if iso is not None:
        return iso.date()

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%b %d, %Y, %I:%M:%S %p",
        "%b %d, %Y, %H:%M:%S",
        "%b %d, %Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_activity_json(path: Path, source: str | None = None) -> ActivitySummary:
    """Parse a generic activity JSON export into an ActivitySummary.

    Accepts a flexible set of key names (Strava-API-like or simple summaries).
    """

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ActivityImportError(f"Could not parse JSON file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ActivityImportError(
            f"Activity JSON must be an object at the top level: {path}."
        )

    distance_km = _json_number(data, ("distance_km",))
    if distance_km is None:
        distance_m = _json_number(data, ("distance_m", "distance_meters", "distance"))
        distance_km = distance_m / 1000 if distance_m else None

    duration_seconds = _json_number(
        data, ("duration_seconds", "moving_time", "elapsed_time")
    )
    if duration_seconds is None:
        duration_seconds = _duration_string_to_seconds(data.get("duration"))

    average_hr = _json_number(data, ("average_heart_rate", "average_hr", "avg_hr"))
    max_hr = _json_number(data, ("max_heart_rate", "max_hr"))
    elevation = _json_number(
        data, ("elevation_gain_m", "total_elevation_gain", "elevation_gain")
    )
    calories = _json_number(data, ("calories",))

    resolved_source = source or _json_source(data)

    return _summary_from_raw(
        distance_km=distance_km,
        duration_seconds=duration_seconds,
        average_heart_rate=average_hr,
        max_heart_rate=max_hr,
        elevation_gain_m=round(elevation, 1) if elevation else None,
        calories=calories,
        source=resolved_source,
    )


def _json_number(data: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key in data and data[key] is not None:
            try:
                return float(data[key])
            except (TypeError, ValueError):
                continue
    return None


def _json_source(data: dict[str, Any]) -> str | None:
    source = data.get("source") or data.get("provider")
    if isinstance(source, str) and source.strip():
        candidate = source.strip().lower()
        return candidate if candidate in VALID_SOURCES else "other"
    return None


def _duration_string_to_seconds(value: Any) -> float | None:
    """Convert a HH:MM:SS or MM:SS string to seconds."""

    if not isinstance(value, str) or not value.strip():
        return None
    parts = value.strip().split(":")
    try:
        numbers = [int(part) for part in parts]
    except ValueError:
        return None
    if len(numbers) == 3:
        hours, minutes, seconds = numbers
    elif len(numbers) == 2:
        hours, minutes, seconds = 0, numbers[0], numbers[1]
    else:
        return None
    return hours * 3600 + minutes * 60 + seconds


# ---------------------------------------------------------------------------
# Format detection and parser registry
# ---------------------------------------------------------------------------


def detect_format(path: Path) -> str:
    """Detect an export's format by extension, falling back to content.

    Returns one of ``tcx``, ``gpx``, ``csv``, ``json``. Raises
    ``ActivityImportError`` for unrecognised inputs.
    """

    suffix = path.suffix.lower().lstrip(".")
    if suffix in ("tcx", "gpx", "csv", "json"):
        return suffix

    try:
        head = path.read_text(encoding="utf-8", errors="ignore").lstrip()
    except OSError as exc:
        raise ActivityImportError(f"Could not read file {path}: {exc}") from exc

    lowered = head.lower()
    if "<trainingcenterdatabase" in lowered or "<activities" in lowered:
        return "tcx"
    if "<gpx" in lowered or "<trk" in lowered:
        return "gpx"
    if head.startswith("{") or head.startswith("["):
        return "json"
    if "," in head.splitlines()[0] if head else False:
        return "csv"
    raise ActivityImportError(
        f"Could not detect the export format for {path}. "
        "Supported: .tcx, .gpx, .csv, .json."
    )


def parse_export(
    path: Path,
    fmt: str,
    activity_date: date | None = None,
    source: str | None = None,
) -> ActivitySummary:
    """Dispatch to the correct parser for a detected format."""

    if fmt == "tcx":
        return parse_tcx(path, source=source or "garmin")
    if fmt == "gpx":
        return parse_gpx(path, source=source or "garmin")
    if fmt == "csv":
        return parse_strava_csv(path, activity_date, source=source or "strava")
    if fmt == "json":
        return parse_activity_json(path, source=source)
    raise ActivityImportError(f"Unsupported export format: {fmt}.")


# ---------------------------------------------------------------------------
# Merge into run.json
# ---------------------------------------------------------------------------


def load_metadata(path: Path) -> dict[str, Any]:
    """Load run metadata from a JSON file."""

    return json.loads(path.read_text(encoding="utf-8"))


def _touch_updated_at(metadata: dict[str, Any]) -> None:
    metadata["updated_at"] = datetime.now(timezone.utc).isoformat()


def merge_summary(
    metadata: dict[str, Any], summary: ActivitySummary, overwrite: bool = False
) -> dict[str, Any]:
    """Merge a parsed ActivitySummary into a metadata dict in place.

    Only the fields the export provides are considered. Existing populated
    values are preserved unless ``overwrite`` is set. ``metrics.source`` is
    updated when the current value is missing or the default ``manual``.
    """

    metrics = metadata.setdefault("metrics", {})
    provided = summary.as_metrics()

    for field in SUMMARY_METRIC_FIELDS:
        if field not in provided:
            continue
        if overwrite or metrics.get(field) is None:
            metrics[field] = provided[field]

    if "source" in provided:
        current_source = metrics.get("source")
        if overwrite or current_source in (None, "manual"):
            metrics["source"] = provided["source"]

    _touch_updated_at(metadata)
    return metadata


# ---------------------------------------------------------------------------
# Weather / gear enrichment
# ---------------------------------------------------------------------------


def _set_if_allowed(
    section: dict[str, Any], field: str, value: Any, overwrite: bool
) -> None:
    """Set ``section[field]`` when a value is provided and the slot is free."""

    if value is None:
        return
    if overwrite or section.get(field) is None:
        section[field] = value


def apply_enrichment(
    metadata: dict[str, Any],
    *,
    weather: str | None = None,
    temperature_c: float | None = None,
    wind: str | None = None,
    shoes: str | None = None,
    watch: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Record weather/gear details into a metadata dict in place.

    Only the provided (non-None) values are considered. Existing populated
    values are preserved unless ``overwrite`` is set.
    """

    conditions = metadata.setdefault("conditions", {})
    _set_if_allowed(conditions, "weather", weather, overwrite)
    _set_if_allowed(conditions, "temperature_c", temperature_c, overwrite)
    _set_if_allowed(conditions, "wind", wind, overwrite)

    gear = metadata.setdefault("gear", {})
    _set_if_allowed(gear, "shoes", shoes, overwrite)
    _set_if_allowed(gear, "watch", watch, overwrite)

    if any(
        value is not None
        for value in (weather, temperature_c, wind, shoes, watch)
    ):
        _touch_updated_at(metadata)
    return metadata


def load_weather_json(path: Path) -> dict[str, Any]:
    """Load weather values from a local JSON file.

    Recognised keys: ``weather``, ``temperature_c`` (or ``temperature``),
    ``wind``. Unknown keys are ignored.
    """

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ActivityImportError(f"Could not parse weather JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ActivityImportError(f"Weather JSON must be an object: {path}.")

    result: dict[str, Any] = {}
    if isinstance(data.get("weather"), str):
        result["weather"] = data["weather"]
    temperature = data.get("temperature_c", data.get("temperature"))
    if temperature is not None:
        try:
            result["temperature_c"] = float(temperature)
        except (TypeError, ValueError):
            pass
    if isinstance(data.get("wind"), str):
        result["wind"] = data["wind"]
    return result


def resolve_shoe(name: str | None, registry_path: Path | None) -> str | None:
    """Resolve a shoe alias to its full name using an optional local registry.

    The registry is a git-ignored JSON object mapping short aliases to full
    shoe names. When no registry is given or the alias is absent, the original
    value is returned unchanged.
    """

    if name is None or registry_path is None:
        return name
    if not registry_path.exists():
        return name
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ActivityImportError(
            f"Could not parse shoe registry {registry_path}: {exc}"
        ) from exc
    if isinstance(registry, dict) and name in registry:
        return str(registry[name])
    return name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import summary metrics from a local activity export into run.json."
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Path to the local activity export (.tcx, .gpx, .csv, .json). "
        "Optional when only recording weather/gear.",
    )
    parser.add_argument(
        "--date",
        required=True,
        type=parse_activity_date,
        help="Recording date as YYYY-MM-DD, or 'today'.",
    )
    parser.add_argument(
        "--root",
        default="content",
        type=Path,
        help="Root directory for content workspaces. Default: content",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Explicit path to the run metadata JSON file. "
        "Defaults to the day's metadata/run.json.",
    )
    parser.add_argument(
        "--source",
        choices=VALID_SOURCES,
        default=None,
        help="Override the recorded metrics.source value.",
    )
    parser.add_argument(
        "--weather",
        default=None,
        help="Weather description, e.g. 'clear', 'light rain'.",
    )
    parser.add_argument(
        "--temperature-c",
        type=float,
        default=None,
        help="Temperature in degrees Celsius.",
    )
    parser.add_argument(
        "--wind",
        default=None,
        help="Wind description, e.g. 'calm', '15 km/h NW'.",
    )
    parser.add_argument(
        "--weather-file",
        type=Path,
        default=None,
        help="Path to a local JSON file with weather values "
        "(weather/temperature_c/wind). CLI flags take precedence.",
    )
    parser.add_argument(
        "--shoes",
        default=None,
        help="Shoes worn. May be a registry alias when --shoe-registry is set.",
    )
    parser.add_argument(
        "--watch",
        default=None,
        help="Watch / device used to record the activity.",
    )
    parser.add_argument(
        "--shoe-registry",
        type=Path,
        default=None,
        help="Optional local JSON registry mapping shoe aliases to full names.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace already-populated metric fields with export values.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the merged metadata without writing it.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validating the metadata against the JSON schema.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    enrichment_provided = any(
        value is not None
        for value in (
            args.weather,
            args.temperature_c,
            args.wind,
            args.weather_file,
            args.shoes,
            args.watch,
        )
    )
    if args.file is None and not enrichment_provided:
        print(
            "Error: provide --file and/or weather/gear flags to update metadata.",
            file=sys.stderr,
        )
        return 1

    fmt: str | None = None
    summary: ActivitySummary | None = None
    if args.file is not None:
        if not args.file.exists():
            print(f"Export file not found: {args.file}", file=sys.stderr)
            return 1
        try:
            fmt = detect_format(args.file)
            summary = parse_export(args.file, fmt, args.date, args.source)
        except ActivityImportError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    # Resolve weather: a local JSON file first, then CLI flags override it.
    weather = args.weather
    temperature_c = args.temperature_c
    wind = args.wind
    try:
        if args.weather_file is not None:
            if not args.weather_file.exists():
                print(
                    f"Weather file not found: {args.weather_file}", file=sys.stderr
                )
                return 1
            from_file = load_weather_json(args.weather_file)
            weather = weather if weather is not None else from_file.get("weather")
            temperature_c = (
                temperature_c
                if temperature_c is not None
                else from_file.get("temperature_c")
            )
            wind = wind if wind is not None else from_file.get("wind")
        shoes = resolve_shoe(args.shoes, args.shoe_registry)
    except ActivityImportError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    metadata_path = args.metadata or metadata_path_for_date(args.date, args.root)
    if metadata_path.exists():
        metadata = load_metadata(metadata_path)
    else:
        metadata = build_default_metadata(args.date)

    if summary is not None:
        merge_summary(metadata, summary, overwrite=args.overwrite)

    apply_enrichment(
        metadata,
        weather=weather,
        temperature_c=temperature_c,
        wind=wind,
        shoes=shoes,
        watch=args.watch,
        overwrite=args.overwrite,
    )

    validate = not args.no_validate
    if validate:
        try:
            validate_metadata(metadata)
        except MetadataValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.dry_run:
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        print(f"\nTarget: {metadata_path}")
        if validate:
            print("Validation: passed")
        return 0

    try:
        write_metadata_file(
            metadata_path, metadata, overwrite=True, validate=False
        )
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    origin = fmt if fmt is not None else "enrichment"
    print(f"Updated metadata file: {metadata_path} (source: {origin})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
