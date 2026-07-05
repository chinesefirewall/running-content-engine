# Metadata Schema

## Purpose

The metadata schema defines the structured information captured for one running or recording day.

This metadata is the bridge between raw footage and later AI-assisted content generation.

It will support future steps such as:

- story brief generation
- platform-specific captions
- video overlay text
- Remotion template props
- MCP-controlled local tools
- Garmin or Strava enrichment

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

This section is likely to become the most important input for the AI story engine.

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
