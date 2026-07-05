#!/usr/bin/env python3
"""Fill a reusable AI prompt template with a day's run metadata.

The prompt library (``prompts/``) holds version-controlled, provider-agnostic
prompt templates. This script loads a chosen template, substitutes ``{{ field }}``
tokens with values from the day's validated ``run.json`` metadata, and writes a
ready-to-paste prompt into the day's ``notes/prompts/`` folder.

Like the rest of the pipeline the generator is deterministic and local-first: it
does not call any external AI service and never publishes anything. The filled
prompt is meant to be pasted by a human into their AI tool of choice. Fields that
are missing from the metadata are filled with a ``TODO`` placeholder.

Example:
    python scripts/create_prompt.py --list
    python scripts/create_prompt.py --prompt daily-run-recap --date 2026-07-05
    python scripts/create_prompt.py --prompt shoe-review --date today --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Allow running this file directly (e.g. `python scripts/create_prompt.py`).
# When executed as a script, Python puts the `scripts/` directory on sys.path
# instead of the project root, which breaks the `scripts.` package import below.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.create_day import build_workspace_plan, parse_activity_date
from scripts.create_metadata import (
    MetadataValidationError,
    validate_metadata,
)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
TODO = "_TODO: add during review._"

# Matches `{{ dotted.path }}` tokens with optional surrounding whitespace.
_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


@dataclass(frozen=True)
class PromptTemplate:
    """A single reusable prompt template loaded from ``prompts/``."""

    id: str
    title: str
    path: Path
    front_matter: dict[str, Any]
    body: str


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a template into its YAML-ish front matter and Markdown body.

    Supports the small subset of YAML used by the prompt templates:
    ``key: value`` scalars and ``key: [a, b, c]`` inline lists. Templates
    without front matter return an empty mapping and the original text.
    """

    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    # First line is the opening `---`; find the closing one.
    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        return {}, text

    front_matter: dict[str, Any] = {}
    for line in lines[1:closing_index]:
        if not line.strip() or ":" not in line:
            continue
        key, _, raw_value = line.partition(":")
        key = key.strip()
        value = raw_value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            items = [item.strip() for item in inner.split(",") if item.strip()]
            front_matter[key] = items
        else:
            front_matter[key] = value

    body = "\n".join(lines[closing_index + 1 :]).lstrip("\n")
    return front_matter, body


def _template_from_file(path: Path) -> PromptTemplate:
    text = path.read_text(encoding="utf-8")
    front_matter, body = parse_front_matter(text)
    prompt_id = str(front_matter.get("id") or path.stem)
    title = str(front_matter.get("title") or prompt_id)
    return PromptTemplate(
        id=prompt_id,
        title=title,
        path=path,
        front_matter=front_matter,
        body=body,
    )


def load_templates(prompts_dir: Path = PROMPTS_DIR) -> list[PromptTemplate]:
    """Load every prompt template from ``prompts_dir`` sorted by id."""

    if not prompts_dir.exists():
        return []

    templates = [_template_from_file(path) for path in sorted(prompts_dir.glob("*.md"))]
    return sorted(templates, key=lambda template: template.id)


def load_template(prompt_id: str, prompts_dir: Path = PROMPTS_DIR) -> PromptTemplate:
    """Load a single template by id.

    Raises:
        KeyError: if no template with the given id exists.
    """

    for template in load_templates(prompts_dir):
        if template.id == prompt_id:
            return template
    raise KeyError(prompt_id)


def load_metadata(path: Path) -> dict[str, Any]:
    """Load run metadata from a JSON file."""

    return json.loads(path.read_text(encoding="utf-8"))


def metadata_path_for_date(activity_date, root: Path) -> Path:
    """Return the default run metadata path for a date and root."""

    plan = build_workspace_plan(activity_date=activity_date, root=root)
    return plan.day_path / "metadata" / "run.json"


def prompt_output_path_for_date(activity_date, root: Path, prompt_id: str) -> Path:
    """Return the default filled-prompt output path for a date and root."""

    plan = build_workspace_plan(activity_date=activity_date, root=root)
    return plan.day_path / "notes" / "prompts" / f"{prompt_id}.md"


def _lookup_field(metadata: dict[str, Any], dotted_path: str) -> Any:
    """Return a nested value from metadata using a dotted path, or None."""

    current: Any = metadata
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _value_or(value: Any, placeholder: str = TODO) -> str:
    """Return a printable value or a placeholder when it is missing."""

    if value is None:
        return placeholder
    text = str(value).strip()
    return text if text else placeholder


def render_template(body: str, metadata: dict[str, Any], placeholder: str = TODO) -> str:
    """Substitute ``{{ dotted.path }}`` tokens in a template body.

    Missing or empty metadata values are replaced with ``placeholder``.
    """

    def replace(match: re.Match[str]) -> str:
        dotted_path = match.group(1)
        return _value_or(_lookup_field(metadata, dotted_path), placeholder)

    return _PLACEHOLDER_RE.sub(replace, body)


def build_prompt(template: PromptTemplate, metadata: dict[str, Any]) -> str:
    """Build the filled prompt document for a template and metadata."""

    date = _value_or(metadata.get("date"))
    rendered = render_template(template.body, metadata).strip()
    lines = [
        f"# Prompt: {template.title}",
        "",
        f"> Filled from run metadata for {date}. "
        "Review, then paste the section below into your AI tool.",
        "",
        "---",
        "",
        rendered,
        "",
    ]
    return "\n".join(lines)


def write_prompt(path: Path, content: str, overwrite: bool = False) -> None:
    """Write the filled prompt Markdown to disk."""

    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Prompt file already exists: {path}. Use --overwrite to replace it."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        content if content.endswith("\n") else content + "\n", encoding="utf-8"
    )


def format_template_list(templates: list[PromptTemplate]) -> str:
    """Format the available templates for terminal output."""

    if not templates:
        return "No prompt templates found."

    lines = ["Available prompts:"]
    for template in templates:
        platforms = template.front_matter.get("platforms") or []
        suffix = f" [{', '.join(platforms)}]" if platforms else ""
        lines.append(f"  - {template.id}: {template.title}{suffix}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fill a reusable AI prompt template with run metadata."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the available prompt templates and exit.",
    )
    parser.add_argument(
        "--prompt",
        help="Id of the prompt template to fill (see --list).",
    )
    parser.add_argument(
        "--date",
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
        help="Replace an existing filled prompt.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the filled prompt without writing it.",
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

    if args.list:
        print(format_template_list(load_templates()))
        return 0

    if not args.prompt:
        print("Error: --prompt is required (or use --list).", file=sys.stderr)
        return 1

    if args.date is None:
        print("Error: --date is required (or use --list).", file=sys.stderr)
        return 1

    try:
        template = load_template(args.prompt)
    except KeyError:
        available = ", ".join(t.id for t in load_templates()) or "(none)"
        print(
            f"Unknown prompt '{args.prompt}'. Available: {available}.",
            file=sys.stderr,
        )
        return 1

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

    content = build_prompt(template, metadata)
    path = prompt_output_path_for_date(args.date, args.root, template.id)

    if args.dry_run:
        print(content)
        print(f"\nTarget: {path}")
        return 0

    try:
        write_prompt(path, content, overwrite=args.overwrite)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Created prompt: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
