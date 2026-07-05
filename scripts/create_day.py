#!/usr/bin/env python3
"""Create the daily local workspace for Running Content Engine.

This script creates a predictable folder structure for one recording day.

Example:
    python scripts/create_day.py --date 2026-07-05
    python scripts/create_day.py --date today --dry-run
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


DEFAULT_SUBDIRECTORIES: tuple[str, ...] = (
    "raw",
    "processed",
    "exports/youtube",
    "exports/instagram",
    "exports/tiktok",
    "exports/facebook",
    "exports/shorts",
    "metadata",
    "notes",
    "thumbnails",
)


@dataclass(frozen=True)
class WorkspacePlan:
    """Planned folder creation for a single recording day."""

    activity_date: date
    root: Path
    directories: tuple[Path, ...]

    @property
    def day_path(self) -> Path:
        return self.root / str(self.activity_date.year) / self.activity_date.isoformat()


def parse_activity_date(value: str) -> date:
    """Parse a date argument.

    Accepted values:
    - today
    - YYYY-MM-DD
    """

    normalized = value.strip().lower()
    if normalized == "today":
        return date.today()

    try:
        return datetime.strptime(normalized, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD or 'today'."
        ) from exc


def build_workspace_plan(
    activity_date: date,
    root: Path,
    subdirectories: tuple[str, ...] = DEFAULT_SUBDIRECTORIES,
) -> WorkspacePlan:
    """Build the directory creation plan without touching the filesystem."""

    normalized_root = root.expanduser().resolve()
    day_path = normalized_root / str(activity_date.year) / activity_date.isoformat()
    directories = tuple(day_path / subdirectory for subdirectory in subdirectories)

    return WorkspacePlan(
        activity_date=activity_date,
        root=normalized_root,
        directories=directories,
    )


def create_workspace(plan: WorkspacePlan, dry_run: bool = False) -> list[Path]:
    """Create directories for a workspace plan.

    Returns the directories that were planned for creation. In dry-run mode the
    filesystem is not changed.
    """

    if dry_run:
        return list(plan.directories)

    for directory in plan.directories:
        directory.mkdir(parents=True, exist_ok=True)

    return list(plan.directories)


def format_plan(plan: WorkspacePlan, dry_run: bool) -> str:
    """Format a workspace plan for terminal output."""

    mode = "DRY RUN" if dry_run else "CREATE"
    lines = [
        f"Mode: {mode}",
        f"Date: {plan.activity_date.isoformat()}",
        f"Workspace: {plan.day_path}",
        "Directories:",
    ]

    for directory in plan.directories:
        lines.append(f"  - {directory}")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a Running Content Engine daily workspace."
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
        "--dry-run",
        action="store_true",
        help="Print the planned directories without creating them.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    plan = build_workspace_plan(activity_date=args.date, root=args.root)
    create_workspace(plan, dry_run=args.dry_run)
    print(format_plan(plan, dry_run=args.dry_run))

    return 0


if __name__ == "__main__":
    sys.exit(main())
