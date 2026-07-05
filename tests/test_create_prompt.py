from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.create_metadata import build_default_metadata, write_metadata_file
from scripts.create_prompt import (
    PROMPTS_DIR,
    build_prompt,
    load_template,
    load_templates,
    parse_front_matter,
    prompt_output_path_for_date,
    render_template,
    write_prompt,
)

EXPECTED_PROMPT_IDS = {
    "daily-run-recap",
    "race-day-recap",
    "shoe-review",
    "weekly-training-summary",
    "health-transformation-story",
    "enrich-content-notes",
}


def _sample_metadata() -> dict:
    metadata = build_default_metadata(date(2026, 7, 5))
    metadata["title_working"] = "Strong finish on tired legs"
    metadata["metrics"].update(
        {
            "distance_km": 18.2,
            "duration": "01:44:00",
            "average_pace": "5:42/km",
            "average_heart_rate": 146,
        }
    )
    metadata["gear"]["shoes"] = "Sample Daily Trainer"
    metadata["content_notes"].update(
        {
            "mood": "started tired, finished strong",
            "lesson": "Energy improved after the first few kilometres.",
            "story_angle": "Showing up on a low-energy morning still pays off.",
            "hook": "I did not feel ready, but the last 5 km changed everything.",
            "key_moment": "The pace felt easier after kilometre 12.",
        }
    )
    return metadata


def test_bundled_templates_are_discoverable() -> None:
    templates = load_templates(PROMPTS_DIR)

    assert {template.id for template in templates} == EXPECTED_PROMPT_IDS


def test_parse_front_matter_splits_metadata_and_body() -> None:
    text = "---\nid: demo\ntitle: Demo\nplatforms: [youtube, tiktok]\n---\nBody {{ date }}\n"

    front_matter, body = parse_front_matter(text)

    assert front_matter["id"] == "demo"
    assert front_matter["title"] == "Demo"
    assert front_matter["platforms"] == ["youtube", "tiktok"]
    assert body.strip() == "Body {{ date }}"


def test_render_template_substitutes_dotted_paths() -> None:
    body = "Distance: {{ metrics.distance_km }} km on {{ date }}"

    rendered = render_template(body, _sample_metadata())

    assert "Distance: 18.2 km on 2026-07-05" in rendered


def test_render_template_uses_placeholder_for_missing_fields() -> None:
    body = "Missing: {{ metrics.does_not_exist }}"

    rendered = render_template(body, _sample_metadata())

    assert "TODO" in rendered


def test_build_prompt_includes_title_and_metadata_values() -> None:
    template = load_template("daily-run-recap")

    content = build_prompt(template, _sample_metadata())

    assert "# Prompt: Daily run recap" in content
    assert "18.2 km" in content
    assert "2026-07-05" in content


def test_load_template_unknown_id_raises() -> None:
    with pytest.raises(KeyError):
        load_template("does-not-exist")


def test_write_prompt_refuses_to_overwrite_without_flag(tmp_path: Path) -> None:
    path = tmp_path / "prompt.md"
    write_prompt(path, "content")

    with pytest.raises(FileExistsError):
        write_prompt(path, "content")


def test_write_prompt_can_overwrite_with_flag(tmp_path: Path) -> None:
    path = tmp_path / "prompt.md"
    write_prompt(path, "first")

    write_prompt(path, "second", overwrite=True)

    assert path.read_text(encoding="utf-8").startswith("second")


def _write_sample_metadata(tmp_path: Path) -> None:
    from scripts.create_prompt import metadata_path_for_date

    run_json = metadata_path_for_date(date(2026, 7, 5), root=tmp_path)
    write_metadata_file(run_json, _sample_metadata())


def test_main_lists_templates(capsys) -> None:
    from scripts.create_prompt import main

    exit_code = main(["--list"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "daily-run-recap" in out


def test_main_creates_prompt_from_metadata(tmp_path: Path) -> None:
    from scripts.create_prompt import main

    _write_sample_metadata(tmp_path)

    exit_code = main(
        ["--prompt", "daily-run-recap", "--date", "2026-07-05", "--root", str(tmp_path)]
    )

    assert exit_code == 0
    output = prompt_output_path_for_date(date(2026, 7, 5), tmp_path, "daily-run-recap")
    assert output.exists()
    assert "18.2 km" in output.read_text(encoding="utf-8")


def test_main_fails_for_unknown_prompt(tmp_path: Path) -> None:
    from scripts.create_prompt import main

    _write_sample_metadata(tmp_path)

    exit_code = main(
        ["--prompt", "nope", "--date", "2026-07-05", "--root", str(tmp_path)]
    )

    assert exit_code == 1


def test_main_fails_when_metadata_missing(tmp_path: Path) -> None:
    from scripts.create_prompt import main

    exit_code = main(
        ["--prompt", "daily-run-recap", "--date", "2026-07-05", "--root", str(tmp_path)]
    )

    assert exit_code == 1


def test_main_dry_run_does_not_write_file(tmp_path: Path) -> None:
    from scripts.create_prompt import main

    _write_sample_metadata(tmp_path)

    exit_code = main(
        [
            "--prompt",
            "daily-run-recap",
            "--date",
            "2026-07-05",
            "--root",
            str(tmp_path),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    output = prompt_output_path_for_date(date(2026, 7, 5), tmp_path, "daily-run-recap")
    assert not output.exists()


def test_main_rejects_invalid_metadata(tmp_path: Path) -> None:
    import json

    from scripts.create_prompt import main, metadata_path_for_date

    run_json = metadata_path_for_date(date(2026, 7, 5), root=tmp_path)
    metadata = _sample_metadata()
    write_metadata_file(run_json, metadata)

    metadata["privacy_level"] = "top_secret"
    run_json.write_text(json.dumps(metadata), encoding="utf-8")

    exit_code = main(
        ["--prompt", "daily-run-recap", "--date", "2026-07-05", "--root", str(tmp_path)]
    )

    assert exit_code == 1
