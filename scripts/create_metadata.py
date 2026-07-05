#!/usr/bin/env python3
"""Create a starter run metadata file for a daily workspace.

Example:
    python scripts/create_metadata.py --date 2026-07-05
    python scripts/create_metadata.py --date today --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow running this file directly (e.g. `python scripts/create_metadata.py`).
# When executed as a script, Python puts the `scripts/` directory on sys.path
# instead of the project root, which breaks the `scripts.` package import below.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.create_day import build_workspace_plan, parse_activity_date

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "run_metadata.schema.json"


class MetadataValidationError(Exception):
    """Raised when metadata does not conform to the run metadata schema."""


def load_schema(schema_path: Path = DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    """Load the run metadata JSON schema from disk."""

    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_metadata(
    metadata: dict[str, Any], schema: dict[str, Any] | None = None
) -> None:
    """Validate metadata against the run metadata JSON schema.

    Raises:
        MetadataValidationError: if the ``jsonschema`` package is unavailable
            or the metadata does not conform to the schema.
    """

    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ModuleNotFoundError as exc:
        raise MetadataValidationError(
            "The 'jsonschema' package is required for metadata validation. "
            "Install it with: pip install jsonschema"
        ) from exc

    if schema is None:
        schema = load_schema()

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(metadata), key=lambda error: list(error.path))
    if errors:
        messages = []
        for error in errors:
            location = "/".join(str(part) for part in error.path) or "<root>"
            messages.append(f"  - {location}: {error.message}")
        raise MetadataValidationError(
            "Metadata failed schema validation:\n" + "\n".join(messages)
        )


def build_default_metadata(activity_date, publish_intent: str = "do_not_publish") -> dict[str, Any]:
    """Build a starter metadata object for one recording day."""

    now = datetime.now(timezone.utc).isoformat()

    return {
        "date": activity_date.isoformat(),
        "activity_type": "run",
        "recording_type": "daily_run",
        "privacy_level": "private",
        "title_working": None,
        "metrics": {
            "distance_km": None,
            "duration": None,
            "average_pace": None,
            "average_heart_rate": None,
            "max_heart_rate": None,
            "elevation_gain_m": None,
            "calories": None,
            "training_effect": None,
            "source": "manual",
        },
        "gear": {
            "shoes": None,
            "camera": None,
            "microphone": None,
            "watch": None,
        },
        "conditions": {
            "weather": None,
            "temperature_c": None,
            "wind": None,
            "surface": None,
            "location_context": None,
        },
        "content_notes": {
            "mood": None,
            "lesson": None,
            "story_angle": None,
            "hook": None,
            "key_moment": None,
            "publish_intent": publish_intent,
        },
        "clips": [],
        "created_at": now,
        "updated_at": now,
    }


def metadata_path_for_date(activity_date, root: Path) -> Path:
    """Return the default metadata file path for a date and root."""

    plan = build_workspace_plan(activity_date=activity_date, root=root)
    return plan.day_path / "metadata" / "run.json"


def write_metadata_file(
    path: Path,
    metadata: dict[str, Any],
    overwrite: bool = False,
    validate: bool = True,
) -> None:
    """Write metadata JSON to disk.

    By default the metadata is validated against the schema before writing, so
    an invalid file is never created on disk.
    """

    if validate:
        validate_metadata(metadata)

    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Metadata file already exists: {path}. Use --overwrite to replace it."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a starter run metadata file.")
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
        "--publish-intent",
        default="do_not_publish",
        choices=("do_not_publish", "draft", "ready_for_review", "published"),
        help="Initial publishing status for the metadata file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing metadata file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the metadata JSON without writing it.",
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

    metadata = build_default_metadata(args.date, publish_intent=args.publish_intent)
    path = metadata_path_for_date(args.date, args.root)
    validate = not args.no_validate

    if validate:
        try:
            validate_metadata(metadata)
        except MetadataValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.dry_run:
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        print(f"\nTarget: {path}")
        if validate:
            print("Validation: passed")
        return 0

    try:
        write_metadata_file(path, metadata, overwrite=args.overwrite, validate=False)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Created metadata file: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
