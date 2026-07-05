#!/usr/bin/env python3
"""Draft content_notes fields for a recording day using an AI provider.

Fills ``content_notes`` (``mood``, ``lesson``, ``story_angle``, ``hook``,
``key_moment``) and ``title_working`` -- the fields the rest of the pipeline
otherwise leaves as a ``TODO`` for a human to fill in ``run.json`` by hand or
via ``scripts/create_prompt.py`` copy/paste. This is the automated
alternative: it reuses the same provider-agnostic prompt library and
templating as ``create_prompt.py``, but calls the provider directly and
merges the parsed draft back into ``run.json``.

Cloud providers (``claude``, ``openai``) need a separate API key -- a ChatGPT
Plus or Claude Pro subscription does not include API access. See
docs/ai-content-enrichment.md for the full design, including exactly what
data is sent to which provider.

Like import_activity.py, this only fills empty fields by default (pass
--overwrite to replace already-populated ones) and never touches
publish_intent: an AI draft never bumps publishing readiness on its own.

Example:
    python scripts/enrich_notes.py --date 2026-07-05
    python scripts/enrich_notes.py --date 2026-07-05 --provider ollama --model llama3.1:8b
    python scripts/enrich_notes.py --date 2026-07-05 --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow running this file directly (e.g. `python scripts/enrich_notes.py`).
# When executed as a script, Python puts the `scripts/` directory on sys.path
# instead of the project root, which breaks the `scripts.` package imports below.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.ai_providers import PROVIDER_NAMES, ProviderError, get_provider
from scripts.create_day import build_workspace_plan, parse_activity_date
from scripts.create_metadata import (
    MetadataValidationError,
    metadata_path_for_date,
    validate_metadata,
    write_metadata_file,
)
from scripts.create_prompt import load_template, render_template
from scripts.create_story_brief import read_notes

ENRICH_PROMPT_ID = "enrich-content-notes"
CONTENT_NOTE_FIELDS: tuple[str, ...] = ("mood", "lesson", "story_angle", "hook", "key_moment")
DRAFT_KEYS: tuple[str, ...] = (*CONTENT_NOTE_FIELDS, "title_working")

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)


class EnrichmentError(Exception):
    """Raised when a provider's response cannot be parsed as the expected draft."""

    def __init__(self, message: str, raw: str | None = None) -> None:
        super().__init__(message)
        self.raw = raw


def load_metadata(path: Path) -> dict[str, Any]:
    """Load run metadata from a JSON file."""

    return json.loads(path.read_text(encoding="utf-8"))


def enrichment_log_path_for_date(activity_date, root: Path, provider: str) -> Path:
    """Return the audit-log path for one day's enrichment run."""

    plan = build_workspace_plan(activity_date=activity_date, root=root)
    return plan.day_path / "notes" / "enrichment-log" / f"{activity_date.isoformat()}-{provider}.json"


def _health_context_lines(metadata: dict[str, Any]) -> list[str]:
    """Format populated health.* fields as prompt lines."""

    health = metadata.get("health") or {}
    lines: list[str] = []
    if health.get("hrv_ms") is not None:
        lines.append(f"- HRV: {health['hrv_ms']} ms")
    if health.get("resting_heart_rate") is not None:
        lines.append(f"- Resting heart rate: {health['resting_heart_rate']} bpm")
    if health.get("sleep_hours") is not None:
        lines.append(f"- Sleep: {health['sleep_hours']} hours")
    if health.get("vo2_max") is not None:
        lines.append(f"- VO2 max: {health['vo2_max']}")
    return lines


def build_enrichment_prompt(
    template, metadata: dict[str, Any], notes: str | None, include_health: bool
) -> str:
    """Render the enrichment prompt from metadata, notes, and optional health context.

    ``health.*`` is deliberately not part of the template file itself -- it is
    appended here only when ``include_health`` is set, so cloud providers
    never see it unless the caller opts in.
    """

    metadata_for_prompt = dict(metadata)
    metadata_for_prompt["notes_freeform"] = notes if notes else "none recorded"
    rendered = render_template(template.body, metadata_for_prompt, placeholder="unknown")

    if include_health:
        health_lines = _health_context_lines(metadata)
        if health_lines:
            rendered += (
                "\n\nHealth context (use only to inform mood/lesson honestly; "
                "do not quote exact numbers back in public captions):\n"
                + "\n".join(health_lines)
            )

    return rendered


def parse_draft(raw: str) -> dict[str, str | None]:
    """Parse a provider's response into the expected draft fields.

    Raises:
        EnrichmentError: if the response is not a JSON object with the
            expected shape.
    """

    text = raw.strip()
    match = _CODE_FENCE_RE.match(text)
    if match:
        text = match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnrichmentError(f"Could not parse response as JSON: {exc}")

    if not isinstance(data, dict):
        raise EnrichmentError("Response JSON must be an object at the top level.")

    draft: dict[str, str | None] = {}
    for key in DRAFT_KEYS:
        value = data.get(key)
        if value is None:
            draft[key] = None
        else:
            text_value = str(value).strip()
            draft[key] = text_value or None
    return draft


def draft_from_provider(provider, prompt: str) -> tuple[dict[str, str | None], str]:
    """Call the provider and parse its response, retrying once on bad JSON.

    Returns the parsed draft and the raw response that produced it.

    Raises:
        EnrichmentError: if the response is still unparseable after one
            retry. The raised error's ``raw`` attribute carries the final
            unparseable response for debugging.
    """

    raw = provider.complete(prompt)
    try:
        return parse_draft(raw), raw
    except EnrichmentError:
        pass

    retry_prompt = (
        prompt
        + "\n\nYour previous response was not valid JSON. "
        "Return ONLY the JSON object described above, with no other text."
    )
    raw = provider.complete(retry_prompt)
    try:
        return parse_draft(raw), raw
    except EnrichmentError as exc:
        raise EnrichmentError(str(exc), raw=raw) from exc


def merge_draft(
    metadata: dict[str, Any],
    draft: dict[str, str | None],
    provider_name: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Merge a parsed draft into metadata, filling empty fields only unless overwrite.

    Never touches publish_intent -- an AI draft never bumps publishing
    readiness on its own.
    """

    content_notes = metadata.setdefault("content_notes", {})
    changed = False

    for field in CONTENT_NOTE_FIELDS:
        value = draft.get(field)
        if value is None:
            continue
        if overwrite or content_notes.get(field) is None:
            content_notes[field] = value
            changed = True

    title = draft.get("title_working")
    if title is not None and (overwrite or metadata.get("title_working") is None):
        metadata["title_working"] = title
        changed = True

    if changed:
        content_notes["draft_source"] = f"ai_{provider_name}"
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()

    return metadata


def is_fully_drafted(metadata: dict[str, Any]) -> bool:
    """Whether every content_notes field and title_working is already populated."""

    content_notes = metadata.get("content_notes") or {}
    if any(content_notes.get(field) is None for field in CONTENT_NOTE_FIELDS):
        return False
    return metadata.get("title_working") is not None


def write_debug_response(path: Path, raw: str) -> None:
    """Save an unparseable raw provider response for debugging."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw, encoding="utf-8")


def write_audit_log(path: Path, prompt: str, raw_response: str, draft: dict[str, Any]) -> None:
    """Save the exact prompt sent and the parsed response for transparency."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"prompt": prompt, "raw_response": raw_response, "parsed_draft": draft}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Draft content_notes fields for a recording day using an AI provider."
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
        "--provider",
        default="claude",
        choices=PROVIDER_NAMES,
        help="AI provider to draft with. Default: claude. Cloud providers "
        "(claude, openai) need a separate API key -- a ChatGPT Plus / Claude "
        "Pro subscription does not include API access.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the provider's default model. Required for --provider openai.",
    )
    parser.add_argument(
        "--include-health-cloud",
        action="store_true",
        help="Also send health.* (HRV, resting heart rate, sleep, VO2 max) to "
        "a cloud provider. Ignored for --provider ollama, which always "
        "includes it locally. Off by default: health data is real personal "
        "health information and stays local unless you opt in.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace already-populated content_notes/title_working fields.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the filled prompt without calling the provider or writing anything.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validating the merged metadata against the JSON schema.",
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

    if not args.overwrite and is_fully_drafted(metadata):
        print(
            f"Content notes already fully drafted for {metadata_path}. "
            "Use --overwrite to regenerate."
        )
        return 0

    try:
        template = load_template(ENRICH_PROMPT_ID)
    except KeyError:
        print(f"Prompt template not found: {ENRICH_PROMPT_ID}", file=sys.stderr)
        return 1

    notes = read_notes(args.date, args.root)
    include_health = args.provider == "ollama" or args.include_health_cloud
    prompt = build_enrichment_prompt(template, metadata, notes, include_health)

    if args.dry_run:
        print(prompt)
        print(f"\n--- Would call provider: {args.provider} ---")
        return 0

    try:
        provider = get_provider(args.provider, model=args.model)
    except ProviderError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        draft, raw_response = draft_from_provider(provider, prompt)
    except ProviderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except EnrichmentError as exc:
        debug_path = enrichment_log_path_for_date(
            args.date, args.root, args.provider
        ).with_suffix(".txt")
        write_debug_response(debug_path, exc.raw or "")
        print(f"{exc} Raw response saved to {debug_path} for debugging.", file=sys.stderr)
        return 1

    merge_draft(metadata, draft, args.provider, overwrite=args.overwrite)

    validate = not args.no_validate
    if validate:
        try:
            validate_metadata(metadata)
        except MetadataValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    try:
        write_metadata_file(metadata_path, metadata, overwrite=True, validate=False)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    audit_path = enrichment_log_path_for_date(args.date, args.root, args.provider)
    write_audit_log(audit_path, prompt, raw_response, draft)

    print(f"Updated metadata file: {metadata_path} (draft_source: ai_{args.provider})")
    print(f"Audit log: {audit_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
