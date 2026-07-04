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

The project is in the foundation stage.

The first implementation target is **daily folder automation**: a repeatable way to create the local workspace for each recording day.

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
  glossary.md
  milestones.md
  requirements.md
  roadmap.md

journal/
  2026/

scripts/
src/
tests/
```

## Privacy notice

This public repository should not contain:

- raw videos
- GPS tracks
- private health data
- API tokens
- personal exports from Garmin or Strava
- unpublished personal media

Sample data should be anonymized or synthetic.
