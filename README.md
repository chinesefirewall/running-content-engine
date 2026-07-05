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

The project has reached its **v1.0 MVP**: a complete local pipeline from a recording day to a review-ready, multi-platform content package.

The run metadata layer is in place: a structured `metadata/run.json` file for each daily workspace, validated against a JSON schema. The **story brief generator** turns metadata and notes into a review-ready draft, and the **content package generator** turns that metadata into platform-specific Markdown files (YouTube, Instagram, TikTok, Facebook, Shorts, and thumbnail ideas) written into the day's `exports/` folders. The **AI prompt library** provides reusable, version-controlled prompt templates in `prompts/` and a renderer that fills a chosen template with the day's metadata for pasting into an AI tool. The **activity importer** parses a local Garmin/Strava export (TCX, GPX, Strava CSV, or activity JSON) and merges only aggregate summary metrics into `run.json`, and can also record weather (typed, or fetched from the internet via `--weather-city`), Apple Health signals (HRV, resting heart rate, sleep, VO2 max via `--health-export`), and gear — deterministically, locally, and without ever storing GPS traces. The **content-notes enrichment step** (`scripts/enrich_notes.py`) drafts mood/lesson/story angle/hook/title via Claude, OpenAI, or a local Ollama model, merging into `run.json` without ever touching `publish_intent`. The **daily pipeline runner** (`scripts/run_day.py`) chains every automated step into one command, and the **manual review and editing workflow** (`docs/manual-review-editing-workflow.md`) defines the human editing step that turns the drafts and raw clips into a finished, publish-ready video.

## New here? Start with the testing playbook

Not sure where the project begins? Follow **`docs/testing-playbook.md`** — a
non-technical, copy-paste, step-by-step guide (with an "expected result" after every
step) that takes you from a fresh Mac to a finished, review-ready content package.
It is written so a non-technical friend can test the whole thing, and it doubles as
the canonical manual test walkthrough. The single entry-point command is
`python scripts/run_day.py --date today`.

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

Or run the whole day's pipeline in one command (create workspace, seed metadata, generate the story brief, and generate the content package):

```bash
python scripts/run_day.py --date 2026-07-05
```

Preview the pipeline plan without running it, and optionally import a local activity export in the same command:

```bash
python scripts/run_day.py --date 2026-07-05 --dry-run
python scripts/run_day.py --date 2026-07-05 --import-file data/sample/garmin-activity.tcx --shoes "Sample Trainer 5"
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

Fetch weather from the internet instead of typing it (no API key needed):

```bash
python scripts/import_activity.py --date 2026-07-05 --weather-city Tallinn --weather-country EE
```

Draft content_notes (mood, lesson, story angle, hook, title) via AI. Needs the
`anthropic` package (`pip install anthropic`, or `pip install -e ".[enrich]"`
for both Claude and OpenAI) and an Anthropic API key (`ANTHROPIC_API_KEY`) --
a Claude Pro subscription does not include API access; see
`docs/ai-content-enrichment.md`:

```bash
python scripts/enrich_notes.py --date 2026-07-05
```

Render a content template (requires Node.js; see `remotion/README.md`):

```bash
cd remotion
npm install
npm run render:daily     # or render:weekly, render:race, render:overlay, render:shoe
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

## End-to-end runbook (MVP)

One recording day, start to finish:

1. **Record** 2 to 3 minutes of clips (see the standard clip structure in `docs/manual-review-editing-workflow.md`).
2. **Run the pipeline** for the day. This creates the workspace, seeds metadata, generates the story brief, and generates the platform content package:
   ```bash
   python scripts/run_day.py --date 2026-07-05
   ```
   To also import metrics from a local Garmin/Strava export, fetch weather, pull Apple Health signals, and draft content_notes via AI in the same run:
   ```bash
   python scripts/run_day.py --date 2026-07-05 \
     --import-file data/sample/garmin-activity.tcx \
     --weather-city Tallinn --weather-country EE \
     --health-export data/private/apple_health/export.xml \
     --shoes "Sample Trainer 5" \
     --enrich --provider claude
   ```
   The runner is idempotent: re-running a day skips steps whose output already exists. Use `--overwrite` to regenerate, and `--dry-run` to preview the plan.
3. **Place raw clips** in `content/YYYY/YYYY-MM-DD/raw/` (kept local, never committed).
4. **Review and edit** using the manual workflow in `docs/manual-review-editing-workflow.md`: read the story brief, pick one angle, edit in Insta360/CapCut, add Remotion data overlays, and export the vertical video into the day's `exports/` folder.
5. **Final human check**: complete the review checklist, set `publish_intent`, and publish.

See `docs/manual-review-editing-workflow.md` for the full review, editing, and publishing checklist.

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
  ai-content-enrichment.md
  content-package.md
  decision-log.md
  folder-structure.md
  glossary.md
  data-integration.md
  manual-review-editing-workflow.md
  metadata-schema.md
  testing-playbook.md
  milestones.md
  prompt-library.md
  remotion-prototype.md
  remotion-templates.md
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
  enrich-content-notes.md

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
  weather.py
  apple_health.py
  ai_providers.py
  enrich_notes.py
  run_day.py

remotion/
  package.json
  remotion.config.ts
  src/
    Root.tsx
    theme.ts
    compositions/
      DailyRunShort.tsx
      WeeklyTrainingRecap.tsx
      RaceDaySummary.tsx
      DataOverlayClip.tsx
      ShoeReviewIntro.tsx
    templates/
      Background.tsx
      MetricRow.tsx
      StatCallout.tsx
      TitleCard.tsx
    data/
      sample-run.json
      sample-week.json
      sample-race.json
      sample-overlay.json
      sample-shoe.json

src/
tests/
```

## Privacy notice

This public repository should not contain raw videos, GPS tracks, tokens, private exports, or unpublished personal media.

Sample data should be anonymized or synthetic.
