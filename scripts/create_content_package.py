#!/usr/bin/env python3
"""Generate a platform-specific content package from run metadata.

The content package turns the structured ``run.json`` metadata (and, when
available, the reviewed ``story-brief.md``) into ready-to-use Markdown files for
each platform, written into the day's ``exports/`` folders.

Like the rest of the pipeline the generator is deterministic and local-first: it
does not call any external AI service and never publishes anything. Every file
is a draft meant to be reviewed and refined by a human before use. Fields that
are missing from the metadata are filled with a ``TODO`` placeholder.

Example:
    python scripts/create_content_package.py --date 2026-07-05
    python scripts/create_content_package.py --date today --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow running this file directly (e.g. `python scripts/create_content_package.py`).
# When executed as a script, Python puts the `scripts/` directory on sys.path
# instead of the project root, which breaks the `scripts.` package import below.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.create_day import build_workspace_plan, parse_activity_date
from scripts.create_metadata import (
    MetadataValidationError,
    validate_metadata,
)

TODO = "_TODO: add during review._"

# Relative paths (from the day workspace) for each generated package file.
PACKAGE_FILES: tuple[str, ...] = (
    "exports/youtube/title.md",
    "exports/youtube/description.md",
    "exports/instagram/caption.md",
    "exports/tiktok/hook.md",
    "exports/facebook/post.md",
    "exports/shorts/hook.md",
    "thumbnails/ideas.md",
)


def load_metadata(path: Path) -> dict[str, Any]:
    """Load run metadata from a JSON file."""

    return json.loads(path.read_text(encoding="utf-8"))


def metadata_path_for_date(activity_date, root: Path) -> Path:
    """Return the default run metadata path for a date and root."""

    plan = build_workspace_plan(activity_date=activity_date, root=root)
    return plan.day_path / "metadata" / "run.json"


def day_path_for_date(activity_date, root: Path) -> Path:
    """Return the day workspace path for a date and root."""

    plan = build_workspace_plan(activity_date=activity_date, root=root)
    return plan.day_path


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


def _overlay_line(metadata: dict[str, Any]) -> str:
    """Build a single-line overlay of the key run stats."""

    metrics = metadata.get("metrics") or {}
    stats: list[str] = []
    if metrics.get("distance_km") is not None:
        stats.append(f"{metrics['distance_km']} km")
    if metrics.get("average_pace"):
        stats.append(f"{metrics['average_pace']}")
    if metrics.get("average_heart_rate") is not None:
        stats.append(f"HR {metrics['average_heart_rate']} bpm")
    return " | ".join(stats) if stats else TODO


def _draft_banner() -> str:
    return "> Draft generated from run metadata. Review before publishing."


def _build_youtube_title(metadata: dict[str, Any]) -> str:
    title_working = _value_or(metadata.get("title_working"))
    lines = [
        "# YouTube Title",
        "",
        _draft_banner(),
        "",
        f"- Primary: {title_working}",
        f"- Alternative: {TODO}",
        "",
    ]
    return "\n".join(lines)


def _build_youtube_description(metadata: dict[str, Any]) -> str:
    content_notes = metadata.get("content_notes") or {}
    summary = _run_summary(metadata)
    story_angle = _value_or(content_notes.get("story_angle"))
    lesson = _value_or(content_notes.get("lesson"))
    lines = [
        "# YouTube Description",
        "",
        _draft_banner(),
        "",
        f"{story_angle}",
        "",
        f"Run summary: {summary}",
        "",
        f"What I learned: {lesson}",
        "",
        "Chapters:",
        f"- 00:00 {TODO}",
        "",
        "Hashtags: " + TODO,
        "",
    ]
    return "\n".join(lines)


def _build_instagram_caption(metadata: dict[str, Any]) -> str:
    content_notes = metadata.get("content_notes") or {}
    hook = _value_or(content_notes.get("hook"))
    lesson = _value_or(content_notes.get("lesson"))
    lines = [
        "# Instagram Caption",
        "",
        _draft_banner(),
        "",
        hook,
        "",
        lesson,
        "",
        "Hashtags: " + TODO,
        "",
    ]
    return "\n".join(lines)


def _build_tiktok_hook(metadata: dict[str, Any]) -> str:
    content_notes = metadata.get("content_notes") or {}
    hook = _value_or(content_notes.get("hook"))
    lines = [
        "# TikTok Hook",
        "",
        _draft_banner(),
        "",
        hook,
        "",
        "Hashtags: " + TODO,
        "",
    ]
    return "\n".join(lines)


def _build_facebook_post(metadata: dict[str, Any]) -> str:
    content_notes = metadata.get("content_notes") or {}
    story_angle = _value_or(content_notes.get("story_angle"))
    lesson = _value_or(content_notes.get("lesson"))
    lines = [
        "# Facebook Post",
        "",
        _draft_banner(),
        "",
        story_angle,
        "",
        lesson,
        "",
    ]
    return "\n".join(lines)


def _build_shorts_hook(metadata: dict[str, Any]) -> str:
    content_notes = metadata.get("content_notes") or {}
    hook = _value_or(content_notes.get("hook"))
    overlay = _overlay_line(metadata)
    lines = [
        "# YouTube Shorts Hook",
        "",
        _draft_banner(),
        "",
        hook,
        "",
        f"On-screen stats: {overlay}",
        "",
        "Hashtags: " + TODO,
        "",
    ]
    return "\n".join(lines)


def _build_thumbnail_ideas(metadata: dict[str, Any]) -> str:
    content_notes = metadata.get("content_notes") or {}
    key_moment = _value_or(content_notes.get("key_moment"))
    overlay = _overlay_line(metadata)
    lines = [
        "# Thumbnail Ideas",
        "",
        _draft_banner(),
        "",
        f"- Highlight the key moment: {key_moment}",
        f"- Text overlay: {overlay}",
        f"- Alternative idea: {TODO}",
        "",
    ]
    return "\n".join(lines)


def build_content_package(metadata: dict[str, Any]) -> dict[str, str]:
    """Build the content package as a mapping of relative path to file content.

    Paths are relative to the day workspace (e.g. ``exports/youtube/title.md``).
    """

    return {
        "exports/youtube/title.md": _build_youtube_title(metadata),
        "exports/youtube/description.md": _build_youtube_description(metadata),
        "exports/instagram/caption.md": _build_instagram_caption(metadata),
        "exports/tiktok/hook.md": _build_tiktok_hook(metadata),
        "exports/facebook/post.md": _build_facebook_post(metadata),
        "exports/shorts/hook.md": _build_shorts_hook(metadata),
        "thumbnails/ideas.md": _build_thumbnail_ideas(metadata),
    }


def write_content_package(
    day_path: Path,
    files: dict[str, str],
    overwrite: bool = False,
) -> list[Path]:
    """Write the content package files under the day workspace.

    Raises ``FileExistsError`` if any target file already exists and
    ``overwrite`` is not set, without writing any files.
    """

    targets = {day_path / relative: content for relative, content in files.items()}

    if not overwrite:
        existing = [path for path in targets if path.exists()]
        if existing:
            joined = ", ".join(str(path) for path in sorted(existing))
            raise FileExistsError(
                f"Content package files already exist: {joined}. "
                "Use --overwrite to replace them."
            )

    written: list[Path] = []
    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            content if content.endswith("\n") else content + "\n",
            encoding="utf-8",
        )
        written.append(path)

    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a platform content package from run metadata."
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
        help="Replace existing content package files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned files and their content without writing them.",
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

    files = build_content_package(metadata)
    day_path = day_path_for_date(args.date, args.root)

    if args.dry_run:
        for relative in PACKAGE_FILES:
            print(f"--- {day_path / relative} ---")
            print(files[relative])
        return 0

    try:
        written = write_content_package(day_path, files, overwrite=args.overwrite)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Created content package ({len(written)} files) under: {day_path}")
    for path in written:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
