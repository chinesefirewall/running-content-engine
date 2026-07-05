# Folder Structure

## Purpose

The daily folder structure is the foundation of the Running Content Engine pipeline.

Every recording day should have a predictable local workspace. This makes later steps easier:

- importing footage
- adding run metadata
- generating story briefs
- preparing platform outputs
- rendering future Remotion templates
- exposing safe local tools through MCP

## Daily workspace convention

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

Example:

```text
content/2026/2026-07-05/
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

## Directory meanings

### `raw/`

Original files copied from the camera, phone, Garmin, Strava, or other sources.

Raw footage and private exports should stay local and should not be committed to GitHub.

### `processed/`

Files that have been renamed, converted, trimmed, stabilized, transcribed, or otherwise prepared for editing.

### `exports/`

Platform-specific final or semi-final outputs.

The first supported platform folders are:

- `youtube/`
- `instagram/`
- `tiktok/`
- `facebook/`
- `shorts/`

### `metadata/`

Structured information about the run or recording day.

Future files may include:

```text
run.json
weather.json
shoes.json
activity-source.json
```

### `notes/`

Human notes, reflections, and story ideas.

Future files may include:

```text
reflection.md
story-brief.md
edit-notes.md
```

### `thumbnails/`

Candidate still images, thumbnail frames, and related design assets.

## Creating a daily workspace

Use the daily folder generator:

```bash
python scripts/create_day.py --date 2026-07-05
```

Use dry-run mode to preview the folders without creating them:

```bash
python scripts/create_day.py --date 2026-07-05 --dry-run
```

Use today's date:

```bash
python scripts/create_day.py --date today
```

## Privacy rule

The `content/` directory is ignored by Git.

This is intentional because the public repository must not contain:

- raw videos
- GPS tracks
- Garmin or Strava private exports
- personal health data
- unpublished personal media
- API tokens or credentials
