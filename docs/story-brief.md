# Story Brief

## Purpose

A story brief is a short, review-ready draft that turns a day's run metadata
(and any free-form notes) into content ideas for each platform.

It is the bridge between structured metadata (`run.json`) and the later
platform-specific content packages.

The generator is deterministic and local-first: it does not call any external
AI service and never publishes anything. The output is always a draft meant to
be reviewed and refined by a human.

## File location

For each daily workspace, the default story brief file is:

```text
content/YYYY/YYYY-MM-DD/notes/story-brief.md
```

## Inputs

The generator reads:

- `content/YYYY/YYYY-MM-DD/metadata/run.json` (validated against the schema)
- any other `.md` files in `content/YYYY/YYYY-MM-DD/notes/` (the generated
  `story-brief.md` itself is ignored)

## Generating a story brief

Create a story brief for a day:

```bash
python scripts/create_story_brief.py --date 2026-07-05
```

Preview without writing:

```bash
python scripts/create_story_brief.py --date 2026-07-05 --dry-run
```

Overwrite an existing brief:

```bash
python scripts/create_story_brief.py --date 2026-07-05 --overwrite
```

Use an explicit metadata file:

```bash
python scripts/create_story_brief.py --date 2026-07-05 --metadata path/to/run.json
```

The run metadata is validated against `schemas/run_metadata.schema.json` before
the brief is generated. Skip validation (not recommended) with `--no-validate`.

## Output sections

The brief includes:

- daily story angle
- YouTube title
- Instagram caption
- TikTok hook
- Facebook post
- overlay text
- thumbnail ideas
- notes
- review checklist

Fields that are missing from the metadata are filled with a `TODO` placeholder
so it is clear what still needs a human touch.

## Manual review

The brief always ends with a review checklist. Nothing is published
automatically. Confirm accuracy and privacy before using any of the generated
text.
