# Running Content Engine

AI-powered pipeline for turning running footage, training data, and daily notes into multi-platform social media content packages.

## Vision

Running Content Engine treats content creation as a data engineering problem.

The goal is to build a low-friction local workflow where one daily recording session can become reusable content for YouTube, Instagram, TikTok, Facebook, and future platforms.

## Why this exists

Manual video editing is repetitive and time-consuming. This project explores how a runner can combine:

- action camera footage
- Garmin or Strava training data
- daily training notes
- AI-generated storylines
- reusable templates
- platform-specific exports

into a sustainable content pipeline.

## Current stage

The project is in the Garmin & Strava data integration stage.

The run metadata layer is in place: a structured `metadata/run.json` file for each daily workspace, validated against a JSON schema. The **story brief generator** turns metadata and notes into a review-ready draft, and the **content package generator** turns that metadata into platform-specific Markdown files (YouTube, Instagram, TikTok, Facebook, Shorts, and thumbnail ideas) written into the day's `exports/` folders. The **AI prompt library** provides reusable, version-controlled prompt templates in `prompts/` and a renderer that fills a chosen template with the day's metadata for pasting into an AI tool. The **activity importer** parses a local Garmin/Strava export (TCX, GPX, Strava CSV, or activity JSON) and merges only aggregate summary metrics into `run.json`, and can also record weather and gear — deterministically, locally, and without ever storing GPS traces.

## Quick start

Install dependencies:

```bash
pip install -e ".[dev]"
```

Create a workspace for a specific date:

```bash
python scripts/create_day.py --date 2026-07-05
```

Create starter metadata for the same date:

```bash
python scripts/create_metadata.py --date 2026-07-05
```

Preview metadata without writing:

```bash
python scripts/create_metadata.py --date 2026-07-05 --dry-run
```

Generate a story brief from the metadata:

```bash
python scripts/create_story_brief.py --date 2026-07-05
```

Generate a platform content package from the metadata:

```bash
python scripts/create_content_package.py --date 2026-07-05
```

List the available AI prompt templates:

```bash
python scripts/create_prompt.py --list
```

Fill a prompt template with the metadata:

```bash
python scripts/create_prompt.py --prompt daily-run-recap --date 2026-07-05
```

Import run metrics from a local Garmin/Strava export:

```bash
python scripts/import_activity.py --file data/sample/garmin-activity.tcx --date 2026-07-05
```

Record the day's weather and shoes (no export needed):

```bash
python scripts/import_activity.py --date 2026-07-05 --weather clear --temperature-c 16 --shoes "Sample Trainer 5"
```

Render the daily run short prototype (requires Node.js; see `remotion/README.md`):

```bash
cd remotion
npm install
npm run render
```

Create a workspace for today:

```bash
python scripts/create_day.py --date today
```

Create metadata for today:

```bash
python scripts/create_metadata.py --date today
```

Run tests:

```bash
python -m pytest
```

## High-level workflow

```text
Record
  -> Import
  -> Organize
  -> Add metadata
  -> Generate story brief
  -> Generate content package
  -> Edit
  -> Export
  -> Publish
```

## Planned daily workspace

```text
content/YYYY/YYYY-MM-DD/
  raw/
  processed/
  exports/
    youtube/
    instagram/
    tiktok/
    facebook/
    shorts/
  metadata/
    run.json
  notes/
  thumbnails/
```

## Project principles

- Record once, reuse many times.
- Reduce repetitive manual editing.
- Keep private data out of Git.
- Start local-first on macOS.
- Keep the architecture modular so tools can be swapped later.
- Use GitHub for lineage, decisions, milestones, and pull requests.

## Repository structure

```text
docs/
  architecture.md
  content-package.md
  decision-log.md
  folder-structure.md
  glossary.md
  data-integration.md
  metadata-schema.md
  milestones.md
  prompt-library.md
  remotion-prototype.md
  requirements.md
  roadmap.md
  story-brief.md

data/
  sample/
    garmin-activity.tcx
    activity.gpx
    strava-activities.csv
    activity.json

examples/
  run_metadata.sample.json

prompts/
  daily-run-recap.md
  race-day-recap.md
  shoe-review.md
  weekly-training-summary.md
  health-transformation-story.md

schemas/
  run_metadata.schema.json

journal/
  2026/

scripts/
  create_day.py
  create_metadata.py
  create_story_brief.py
  create_content_package.py
  create_prompt.py
  import_activity.py

remotion/
  package.json
  remotion.config.ts
  src/
    Root.tsx
    compositions/
      DailyRunShort.tsx
    templates/
      MetricRow.tsx
      TitleCard.tsx
    data/
      sample-run.json

src/
tests/
```

## Privacy notice

This public repository should not contain raw videos, GPS tracks, tokens, private exports, or unpublished personal media.

Sample data should be anonymized or synthetic.
