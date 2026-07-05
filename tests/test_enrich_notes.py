from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from scripts.ai_providers import ProviderError
from scripts.create_metadata import build_default_metadata, write_metadata_file
from scripts.create_prompt import load_template
from scripts.enrich_notes import (
    ENRICH_PROMPT_ID,
    EnrichmentError,
    build_enrichment_prompt,
    draft_from_provider,
    is_fully_drafted,
    main,
    merge_draft,
    parse_draft,
)


class _StubProvider:
    """A fake AIProvider that returns canned responses in order."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._responses.pop(0)


VALID_DRAFT_JSON = json.dumps(
    {
        "mood": "steady",
        "lesson": "Consistency beats intensity.",
        "story_angle": "Another quiet deposit into the fitness account.",
        "hook": "Nothing dramatic today. That was the point.",
        "key_moment": "Held pace through kilometre 8.",
        "title_working": "Easy 10k, steady legs",
    }
)


def _metadata_path(tmp_path: Path, activity_date: date = date(2026, 7, 5)) -> Path:
    return tmp_path / str(activity_date.year) / activity_date.isoformat() / "metadata" / "run.json"


# ---------------------------------------------------------------------------
# parse_draft
# ---------------------------------------------------------------------------


def test_parse_draft_reads_plain_json() -> None:
    draft = parse_draft(VALID_DRAFT_JSON)

    assert draft["mood"] == "steady"
    assert draft["title_working"] == "Easy 10k, steady legs"


def test_parse_draft_strips_markdown_code_fence() -> None:
    fenced = f"```json\n{VALID_DRAFT_JSON}\n```"

    draft = parse_draft(fenced)

    assert draft["mood"] == "steady"


def test_parse_draft_maps_null_and_missing_to_none() -> None:
    raw = json.dumps({"mood": None, "lesson": "  ", "story_angle": "true angle"})

    draft = parse_draft(raw)

    assert draft["mood"] is None
    # Whitespace-only strings are treated as missing, not a real value.
    assert draft["lesson"] is None
    assert draft["story_angle"] == "true angle"
    assert draft["hook"] is None
    assert draft["title_working"] is None


def test_parse_draft_rejects_invalid_json() -> None:
    with pytest.raises(EnrichmentError):
        parse_draft("not json at all")


def test_parse_draft_rejects_non_object_json() -> None:
    with pytest.raises(EnrichmentError):
        parse_draft("[1, 2, 3]")


# ---------------------------------------------------------------------------
# draft_from_provider
# ---------------------------------------------------------------------------


def test_draft_from_provider_succeeds_on_first_response() -> None:
    provider = _StubProvider([VALID_DRAFT_JSON])

    draft, raw = draft_from_provider(provider, "prompt text")

    assert draft["mood"] == "steady"
    assert raw == VALID_DRAFT_JSON
    assert len(provider.prompts) == 1


def test_draft_from_provider_retries_once_on_bad_json() -> None:
    provider = _StubProvider(["not json", VALID_DRAFT_JSON])

    draft, raw = draft_from_provider(provider, "prompt text")

    assert draft["mood"] == "steady"
    assert len(provider.prompts) == 2
    # The retry prompt must still contain the original prompt content.
    assert "prompt text" in provider.prompts[1]


def test_draft_from_provider_raises_with_raw_after_second_failure() -> None:
    provider = _StubProvider(["not json", "still not json"])

    with pytest.raises(EnrichmentError) as exc_info:
        draft_from_provider(provider, "prompt text")

    assert exc_info.value.raw == "still not json"


# ---------------------------------------------------------------------------
# merge_draft
# ---------------------------------------------------------------------------


def test_merge_draft_fills_empty_fields_only_by_default() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["content_notes"]["mood"] = "already set by hand"
    draft = parse_draft(VALID_DRAFT_JSON)

    merge_draft(metadata, draft, "claude")

    assert metadata["content_notes"]["mood"] == "already set by hand"
    assert metadata["content_notes"]["lesson"] == "Consistency beats intensity."
    assert metadata["title_working"] == "Easy 10k, steady legs"
    assert metadata["content_notes"]["draft_source"] == "ai_claude"


def test_merge_draft_overwrite_replaces_existing_values() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["content_notes"]["mood"] = "already set by hand"
    draft = parse_draft(VALID_DRAFT_JSON)

    merge_draft(metadata, draft, "openai", overwrite=True)

    assert metadata["content_notes"]["mood"] == "steady"
    assert metadata["content_notes"]["draft_source"] == "ai_openai"


def test_merge_draft_never_touches_publish_intent() -> None:
    metadata = build_default_metadata(date(2026, 7, 5), publish_intent="draft")
    draft = parse_draft(VALID_DRAFT_JSON)

    merge_draft(metadata, draft, "claude")

    assert metadata["content_notes"]["publish_intent"] == "draft"


# ---------------------------------------------------------------------------
# is_fully_drafted
# ---------------------------------------------------------------------------


def test_is_fully_drafted_false_for_default_metadata() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))

    assert is_fully_drafted(metadata) is False


def test_is_fully_drafted_true_once_all_fields_present() -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    draft = parse_draft(VALID_DRAFT_JSON)

    merge_draft(metadata, draft, "claude")

    assert is_fully_drafted(metadata) is True


# ---------------------------------------------------------------------------
# build_enrichment_prompt
# ---------------------------------------------------------------------------


def test_build_enrichment_prompt_excludes_health_by_default() -> None:
    template = load_template(ENRICH_PROMPT_ID)
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["health"] = {"hrv_ms": 45.0, "resting_heart_rate": 52, "sleep_hours": 7.0, "vo2_max": None}

    prompt = build_enrichment_prompt(template, metadata, notes=None, include_health=False)

    assert "HRV" not in prompt
    assert "none recorded" in prompt


def test_build_enrichment_prompt_includes_health_when_allowed() -> None:
    template = load_template(ENRICH_PROMPT_ID)
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["health"] = {"hrv_ms": 45.0, "resting_heart_rate": 52, "sleep_hours": 7.0, "vo2_max": None}

    prompt = build_enrichment_prompt(template, metadata, notes="Felt tired at the start.", include_health=True)

    assert "HRV: 45.0 ms" in prompt
    assert "Resting heart rate: 52 bpm" in prompt
    assert "Sleep: 7.0 hours" in prompt
    assert "Felt tired at the start." in prompt


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def test_main_fails_when_metadata_missing(tmp_path: Path) -> None:
    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 1


def test_main_skips_when_already_fully_drafted(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    draft = parse_draft(VALID_DRAFT_JSON)
    merge_draft(metadata, draft, "claude")
    write_metadata_file(_metadata_path(tmp_path), metadata)

    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 0
    assert "already fully drafted" in capsys.readouterr().out


def test_main_dry_run_prints_prompt_without_calling_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    write_metadata_file(_metadata_path(tmp_path), metadata)

    def _fail_get_provider(*args: object, **kwargs: object) -> None:
        raise AssertionError("get_provider must not be called during --dry-run")

    monkeypatch.setattr("scripts.enrich_notes.get_provider", _fail_get_provider)

    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path), "--dry-run"])

    assert exit_code == 0
    assert "Would call provider: claude" in capsys.readouterr().out


def test_main_writes_draft_and_audit_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata_path = _metadata_path(tmp_path)
    write_metadata_file(metadata_path, metadata)

    stub = _StubProvider([VALID_DRAFT_JSON])
    monkeypatch.setattr("scripts.enrich_notes.get_provider", lambda name, model=None: stub)

    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path), "--provider", "claude"])

    assert exit_code == 0
    saved = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert saved["content_notes"]["mood"] == "steady"
    assert saved["content_notes"]["draft_source"] == "ai_claude"
    assert saved["content_notes"]["publish_intent"] == "do_not_publish"

    audit_path = tmp_path / "2026" / "2026-07-05" / "notes" / "enrichment-log" / "2026-07-05-claude.json"
    assert audit_path.exists()
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["raw_response"] == VALID_DRAFT_JSON


def test_main_provider_error_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    write_metadata_file(_metadata_path(tmp_path), metadata)

    def _raise_provider_error(*args: object, **kwargs: object) -> None:
        raise ProviderError("no key configured")

    monkeypatch.setattr("scripts.enrich_notes.get_provider", _raise_provider_error)

    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path)])

    assert exit_code == 1


def test_main_saves_debug_file_when_response_never_parses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metadata = build_default_metadata(date(2026, 7, 5))
    write_metadata_file(_metadata_path(tmp_path), metadata)

    stub = _StubProvider(["not json", "still not json"])
    monkeypatch.setattr("scripts.enrich_notes.get_provider", lambda name, model=None: stub)

    exit_code = main(["--date", "2026-07-05", "--root", str(tmp_path), "--provider", "claude"])

    assert exit_code == 1
    debug_path = tmp_path / "2026" / "2026-07-05" / "notes" / "enrichment-log" / "2026-07-05-claude.txt"
    assert debug_path.read_text(encoding="utf-8") == "still not json"
