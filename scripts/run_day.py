#!/usr/bin/env python3
"""Run the full daily content pipeline end to end for one recording day.

This orchestrator chains the individual pipeline steps in the correct order so a
single command drives a whole recording day:

    create_day
      -> create_metadata
      -> import_activity            (only when import/enrichment flags are given)
      -> create_story_brief
      -> create_content_package

Each step is the same script that can be run by hand; this wrapper simply calls
them in sequence. It is idempotent: by default a step is skipped when its output
already exists, so re-running the same day is safe. Pass --overwrite to force
every step to regenerate its output.

Example:
    python scripts/run_day.py --date 2026-07-05
    python scripts/run_day.py --date today --dry-run
    python scripts/run_day.py --date 2026-07-05 \
        --import-file data/sample/garmin-activity.tcx --shoes "Sample Trainer 5"
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

# Allow running this file directly (e.g. `python scripts/run_day.py`).
# When executed as a script, Python puts the `scripts/` directory on sys.path
# instead of the project root, which breaks the `scripts.` package imports below.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import (
    create_content_package,
    create_day,
    create_metadata,
    create_story_brief,
    import_activity,
)
from scripts.create_content_package import PACKAGE_FILES, day_path_for_date
from scripts.create_day import parse_activity_date
from scripts.create_metadata import metadata_path_for_date
from scripts.create_story_brief import story_brief_path_for_date


@dataclass
class Step:
    """One pipeline step the orchestrator can run or preview.

    ``run`` calls the underlying script's ``main`` with ``argv`` and returns its
    exit code. ``skip`` decides whether the step's output already exists (used to
    keep re-runs idempotent unless the caller passes --overwrite).
    """

    name: str
    argv: list[str]
    run: Callable[[list[str]], int]
    skip: Callable[[], bool] = field(default=lambda: False)

    def command(self) -> str:
        return "python scripts/" + " ".join([self.name + ".py", *self.argv])


def _common_argv(activity_date: date, root: Path) -> list[str]:
    return ["--date", activity_date.isoformat(), "--root", str(root)]


def build_steps(args: argparse.Namespace) -> list[Step]:
    """Build the ordered list of steps for one recording day."""

    activity_date: date = args.date
    root: Path = args.root
    base = _common_argv(activity_date, root)

    metadata_path = metadata_path_for_date(activity_date, root)
    story_brief_path = story_brief_path_for_date(activity_date, root)
    day_path = day_path_for_date(activity_date, root)
    package_paths = [day_path / relative for relative in PACKAGE_FILES]

    steps: list[Step] = []

    # 1. Create the daily workspace. mkdir is idempotent, so this always runs.
    steps.append(
        Step(
            name="create_day",
            argv=list(base),
            run=create_day.main,
        )
    )

    # 2. Seed starter metadata. Skipped when run.json already exists.
    metadata_argv = [*base, "--publish-intent", args.publish_intent]
    if args.overwrite:
        metadata_argv.append("--overwrite")
    if args.no_validate:
        metadata_argv.append("--no-validate")
    steps.append(
        Step(
            name="create_metadata",
            argv=metadata_argv,
            run=create_metadata.main,
            skip=lambda: metadata_path.exists(),
        )
    )

    # 3. Import activity metrics / record weather and gear. Only when requested.
    #    import_activity merges into existing fields and has its own overwrite
    #    semantics, so it is never auto-skipped.
    if _import_requested(args):
        import_argv = list(base)
        if args.import_file is not None:
            import_argv += ["--file", str(args.import_file)]
        if args.weather is not None:
            import_argv += ["--weather", args.weather]
        if args.temperature_c is not None:
            import_argv += ["--temperature-c", str(args.temperature_c)]
        if args.shoes is not None:
            import_argv += ["--shoes", args.shoes]
        if args.overwrite:
            import_argv.append("--overwrite")
        if args.no_validate:
            import_argv.append("--no-validate")
        steps.append(
            Step(
                name="import_activity",
                argv=import_argv,
                run=import_activity.main,
            )
        )

    # 4. Generate the story brief. Skipped when it already exists.
    brief_argv = list(base)
    if args.overwrite:
        brief_argv.append("--overwrite")
    if args.no_validate:
        brief_argv.append("--no-validate")
    steps.append(
        Step(
            name="create_story_brief",
            argv=brief_argv,
            run=create_story_brief.main,
            skip=lambda: story_brief_path.exists(),
        )
    )

    # 5. Generate the platform content package. Skipped once every file exists.
    package_argv = list(base)
    if args.overwrite:
        package_argv.append("--overwrite")
    if args.no_validate:
        package_argv.append("--no-validate")
    steps.append(
        Step(
            name="create_content_package",
            argv=package_argv,
            run=create_content_package.main,
            skip=lambda: all(path.exists() for path in package_paths),
        )
    )

    return steps


def _import_requested(args: argparse.Namespace) -> bool:
    """Whether the caller supplied any import/enrichment input."""

    return any(
        value is not None
        for value in (args.import_file, args.weather, args.temperature_c, args.shoes)
    )


def run_pipeline(steps: list[Step], overwrite: bool = False) -> int:
    """Run the steps in order, stopping at the first failure.

    Returns 0 on success, or the failing step's non-zero exit code.
    """

    for step in steps:
        if not overwrite and step.skip():
            print(f"[skip] {step.name}: output already exists (use --overwrite to regenerate)")
            continue

        print(f"[run ] {step.command()}")
        exit_code = step.run(step.argv)
        if exit_code != 0:
            print(f"[fail] {step.name} exited with code {exit_code}", file=sys.stderr)
            return exit_code

    return 0


def print_plan(steps: list[Step], overwrite: bool) -> None:
    """Print the ordered plan of commands without running anything."""

    print("Mode: DRY RUN (no steps executed)")
    print("Planned steps:")
    for index, step in enumerate(steps, start=1):
        marker = "skip" if (not overwrite and step.skip()) else "run "
        print(f"  {index}. [{marker}] {step.command()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full daily content pipeline end to end for one day."
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
        "--publish-intent",
        default="do_not_publish",
        choices=("do_not_publish", "draft", "ready_for_review", "published"),
        help="Initial publishing status for new metadata. Default: do_not_publish",
    )
    parser.add_argument(
        "--import-file",
        type=Path,
        default=None,
        help="Optional local activity export (.tcx, .gpx, .csv, .json) to import.",
    )
    parser.add_argument(
        "--weather",
        default=None,
        help="Optional weather description to record, e.g. 'clear'.",
    )
    parser.add_argument(
        "--temperature-c",
        type=float,
        default=None,
        help="Optional temperature in degrees Celsius to record.",
    )
    parser.add_argument(
        "--shoes",
        default=None,
        help="Optional shoes worn to record.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Force every step to regenerate its output.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validating metadata against the JSON schema in each step.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the ordered plan of steps without running them.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    steps = build_steps(args)

    if args.dry_run:
        print_plan(steps, overwrite=args.overwrite)
        return 0

    print(f"Running daily pipeline for {args.date.isoformat()}")
    exit_code = run_pipeline(steps, overwrite=args.overwrite)

    if exit_code == 0:
        print(f"Done. Daily pipeline complete for {args.date.isoformat()}.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
