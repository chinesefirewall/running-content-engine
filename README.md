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

The project is in the story brief stage.

The run metadata layer is in place: a structured `metadata/run.json` file for each daily workspace, validated against a JSON schema. The current implementation target is the **story brief generator**, which turns metadata and notes into a review-ready content draft.

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
  decision-log.md
  folder-structure.md
  glossary.md
  metadata-schema.md
  milestones.md
  requirements.md
  roadmap.md
  story-brief.md

examples/
  run_metadata.sample.json

schemas/
  run_metadata.schema.json

journal/
  2026/

scripts/
  create_day.py
  create_metadata.py
  create_story_brief.py

src/
tests/
```

## Privacy notice

This public repository should not contain raw videos, GPS tracks, tokens, private exports, or unpublished personal media.

Sample data should be anonymized or synthetic.
