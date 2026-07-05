# Metadata Schema

## Purpose

The metadata schema defines the structured information captured for one running or recording day.

This metadata is the bridge between raw footage and later AI-assisted content generation.

It supports:

- story brief generation
- platform-specific captions
- video overlay text
- Remotion template props
- Garmin/Strava/Apple Health enrichment (`scripts/import_activity.py`)
- AI-assisted content-notes drafting (`scripts/enrich_notes.py`)

And future steps such as:

- MCP-controlled local tools

## File location

For each daily workspace, the default metadata file is:

```text
content/YYYY/YYYY-MM-DD/metadata/run.json
```

Example:

```text
content/2026/2026-07-05/metadata/run.json
```

## Schema location

The JSON schema is stored at:

```text
schemas/run_metadata.schema.json
```

A public-safe sample file is stored at:

```text
examples/run_metadata.sample.json
```

## Creating starter metadata

Create a starter metadata file:

```bash
python scripts/create_metadata.py --date 2026-07-05
```

Preview without writing:

```bash
python scripts/create_metadata.py --date 2026-07-05 --dry-run
```

Use today's date:

```bash
python scripts/create_metadata.py --date today
```

Overwrite an existing file:

```bash
python scripts/create_metadata.py --date 2026-07-05 --overwrite
```

## Validation

The generator validates metadata against `schemas/run_metadata.schema.json`
before writing it, so an invalid `run.json` is never created on disk.
Validation uses the [`jsonschema`](https://pypi.org/project/jsonschema/)
package (declared in `pyproject.toml`).

If validation fails, the command prints the offending fields and exits with a
non-zero status without writing the file.

Skip validation (not recommended) with:

```bash
python scripts/create_metadata.py --date 2026-07-05 --no-validate
```

## Required top-level fields

The schema requires:

- `date`
- `activity_type`
- `recording_type`
- `privacy_level`
- `metrics`
- `content_notes`

## Important fields

### `privacy_level`

Controls how carefully the metadata should be handled.

Allowed values:

- `public_safe`
- `private`
- `sensitive`

Use `public_safe` only for synthetic or anonymized examples.

Use `private` for real day-to-day local data.

Use `sensitive` for anything involving health details, exact location traces, immigration/legal context, or other private information.

### `content_notes`

This section captures the human story.

Important fields:

- `mood`
- `lesson`
- `story_angle`
- `hook`
- `key_moment`
- `publish_intent`
- `draft_source` — who wrote these fields: `manual` (or `null`), `ai_claude`,
  `ai_openai`, or `ai_ollama`. Set automatically by `scripts/enrich_notes.py`;
  never set by hand. Review AI-drafted notes for truthfulness before treating
  them as final (see `docs/manual-review-editing-workflow.md`).

This section is likely to become the most important input for the AI story engine.

### `health`

Optional. Populated by `scripts/import_activity.py --health-export` from an
Apple Health `export.xml` (see `docs/data-integration.md`). Every field is
nullable and absent by default.

- `hrv_ms` — heart rate variability (SDNN), in milliseconds.
- `resting_heart_rate` — beats per minute.
- `sleep_hours` — hours asleep the night before the run.
- `vo2_max`
- `source` — `apple_health` or `manual`.

This is real personal health data. It is excluded from prompts sent to cloud
AI providers by default (`scripts/enrich_notes.py`); only `--provider ollama`
(fully local) or an explicit `--include-health-cloud` flag includes it.

### `clips`

The `clips` array maps known clip labels to filenames.

Recommended labels:

- `morning_intro`
- `run_clip`
- `finish_reflection`
- `b_roll`
- `other`

## Privacy rules

Do not commit real metadata from the `content/` directory.

The public repository should contain only:

- schemas
- synthetic examples
- documentation
- code
- tests

Avoid committing:

- exact GPS traces
- private health data
- raw Garmin or Strava exports
- raw videos
- unpublished personal content
- API tokens or credentials
