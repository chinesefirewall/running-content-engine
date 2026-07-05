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

from scripts.create_day import build_workspace_plan, parse_activity_date


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


def write_metadata_file(path: Path, metadata: dict[str, Any], overwrite: bool = False) -> None:
    """Write metadata JSON to disk."""

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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    metadata = build_default_metadata(args.date, publish_intent=args.publish_intent)
    path = metadata_path_for_date(args.date, args.root)

    if args.dry_run:
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        print(f"\nTarget: {path}")
        return 0

    try:
        write_metadata_file(path, metadata, overwrite=args.overwrite)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Created metadata file: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
