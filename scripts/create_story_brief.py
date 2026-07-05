#!/usr/bin/env python3
"""Generate a daily story brief from run metadata and notes.

The story brief is a review-ready Markdown draft that turns the structured
``run.json`` metadata (and any free-form notes) into content ideas for each
platform. It never publishes anything; the output is meant to be reviewed and
refined by a human before use.

Example:
    python scripts/create_story_brief.py --date 2026-07-05
    python scripts/create_story_brief.py --date today --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow running this file directly (e.g. `python scripts/create_story_brief.py`).
# When executed as a script, Python puts the `scripts/` directory on sys.path
# instead of the project root, which breaks the `scripts.` package import below.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.create_day import build_workspace_plan, parse_activity_date
from scripts.create_metadata import (
    MetadataValidationError,
    validate_metadata,
)

DEFAULT_STORY_BRIEF_FILENAME = "story-brief.md"
TODO = "_TODO: add during review._"


def load_metadata(path: Path) -> dict[str, Any]:
    """Load run metadata from a JSON file."""

    return json.loads(path.read_text(encoding="utf-8"))


def metadata_path_for_date(activity_date, root: Path) -> Path:
    """Return the default run metadata path for a date and root."""

    plan = build_workspace_plan(activity_date=activity_date, root=root)
    return plan.day_path / "metadata" / "run.json"


def story_brief_path_for_date(activity_date, root: Path) -> Path:
    """Return the default story brief path for a date and root."""

    plan = build_workspace_plan(activity_date=activity_date, root=root)
    return plan.day_path / "notes" / DEFAULT_STORY_BRIEF_FILENAME


def read_notes(activity_date, root: Path) -> str | None:
    """Read free-form Markdown notes for a day, if any.

    Reads every ``.md`` file in the day's ``notes`` directory except the
    generated story brief itself. Returns ``None`` when no notes exist.
    """

    plan = build_workspace_plan(activity_date=activity_date, root=root)
    notes_dir = plan.day_path / "notes"
    if not notes_dir.exists():
        return None

    fragments: list[str] = []
    for note_file in sorted(notes_dir.glob("*.md")):
        if note_file.name == DEFAULT_STORY_BRIEF_FILENAME:
            continue
        text = note_file.read_text(encoding="utf-8").strip()
        if text:
            fragments.append(text)

    if not fragments:
        return None

    return "\n\n".join(fragments)


def _value_or(value: Any, placeholder: str = TODO) -> str:
    """Return a printable value or a placeholder when it is missing."""

    if value is None:
        return placeholder
    text = str(value).strip()
    return text if text else placeholder


def _run_summary(metadata: dict[str, Any]) -> str:
    """Build a short, human-readable summary of the run's key metrics."""

    metrics = metadata.get("metrics") or {}
    parts: list[str] = []

    distance = metrics.get("distance_km")
    if distance is not None:
        parts.append(f"{distance} km")

    activity = metadata.get("activity_type")
    if activity:
        parts.append(str(activity))

    pace = metrics.get("average_pace")
    if pace:
        parts.append(f"at {pace}")

    duration = metrics.get("duration")
    if duration:
        parts.append(f"in {duration}")

    if not parts:
        return TODO

    return " ".join(parts)


def build_story_brief(metadata: dict[str, Any], notes: str | None = None) -> str:
    """Build the Markdown story brief from metadata and optional notes."""

    content_notes = metadata.get("content_notes") or {}
    metrics = metadata.get("metrics") or {}

    date = _value_or(metadata.get("date"))
    story_angle = _value_or(content_notes.get("story_angle"))
    hook = _value_or(content_notes.get("hook"))
    mood = _value_or(content_notes.get("mood"))
    lesson = _value_or(content_notes.get("lesson"))
    key_moment = _value_or(content_notes.get("key_moment"))
    title_working = _value_or(metadata.get("title_working"))
    summary = _run_summary(metadata)

    overlay_stats: list[str] = []
    if metrics.get("distance_km") is not None:
        overlay_stats.append(f"{metrics['distance_km']} km")
    if metrics.get("average_pace"):
        overlay_stats.append(f"{metrics['average_pace']}")
    if metrics.get("average_heart_rate") is not None:
        overlay_stats.append(f"HR {metrics['average_heart_rate']} bpm")
    overlay_line = " | ".join(overlay_stats) if overlay_stats else TODO

    lines = [
        f"# Story Brief - {date}",
        "",
        "> Draft generated from run metadata. Review and refine before publishing.",
        "",
        f"- Activity summary: {summary}",
        f"- Working title: {title_working}",
        f"- Mood: {mood}",
        "",
        "## Daily story angle",
        "",
        story_angle,
        "",
        "## YouTube title",
        "",
        f"- {title_working}",
        f"- Alternative: {TODO}",
        "",
        "## Instagram caption",
        "",
        hook,
        "",
        lesson,
        "",
        "Hashtags: " + TODO,
        "",
        "## TikTok hook",
        "",
        hook,
        "",
        "## Facebook post",
        "",
        story_angle,
        "",
        lesson,
        "",
        "## Overlay text",
        "",
        f"- Stats: {overlay_line}",
        f"- Key moment: {key_moment}",
        "",
        "## Thumbnail ideas",
        "",
        f"- Highlight the key moment: {key_moment}",
        f"- Text overlay: {overlay_line}",
        f"- Alternative idea: {TODO}",
        "",
        "## Notes",
        "",
        notes.strip() if notes else "_No notes recorded for this day._",
        "",
        "## Review checklist",
        "",
        "- [ ] Story angle reflects the real day",
        "- [ ] Titles and captions are accurate and non-clickbait",
        "- [ ] No private location, health, or personal data exposed",
        "- [ ] Overlay stats match the metrics",
        "- [ ] Approved for the intended platforms",
        "",
    ]

    return "\n".join(lines)


def write_story_brief(path: Path, content: str, overwrite: bool = False) -> None:
    """Write the story brief Markdown to disk."""

    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Story brief already exists: {path}. Use --overwrite to replace it."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a daily story brief from run metadata and notes."
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
        "--overwrite",
        action="store_true",
        help="Replace an existing story brief.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the story brief without writing it.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validating the run metadata against the JSON schema.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    metadata_path = args.metadata or metadata_path_for_date(args.date, args.root)
    if not metadata_path.exists():
        print(
            f"Run metadata not found: {metadata_path}. "
            "Create it first with scripts/create_metadata.py.",
            file=sys.stderr,
        )
        return 1

    metadata = load_metadata(metadata_path)

    if not args.no_validate:
        try:
            validate_metadata(metadata)
        except MetadataValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    notes = read_notes(args.date, args.root)
    content = build_story_brief(metadata, notes=notes)
    path = story_brief_path_for_date(args.date, args.root)

    if args.dry_run:
        print(content)
        print(f"\nTarget: {path}")
        return 0

    try:
        write_story_brief(path, content, overwrite=args.overwrite)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Created story brief: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
