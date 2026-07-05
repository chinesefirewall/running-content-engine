# Architecture

## Overview

Running Content Engine treats content creation as a data pipeline.

The system converts raw inputs into reusable content outputs through a repeatable workflow.

```text
Camera footage
    +
Run data
    +
Daily notes
    ↓
File organization
    ↓
Metadata layer
    ↓
Story engine
    ↓
Content package generator
    ↓
Editing workflow
    ↓
Platform exports
```

## Core components

### 1. Media ingestion

Responsible for importing raw video files from an action camera or phone.

The initial version can be manual: the user places files into the correct daily `raw/` folder.

Future versions may automate file detection, copying, renaming, and clip classification.

### 2. Folder automation

Creates a consistent daily folder structure.

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

This is the first implementation milestone because every later step depends on a stable workspace.

### 3. Metadata collector

Stores structured information about each run or recording day.

Possible sources:

- manual notes
- Garmin export
- Strava export
- weather data
- shoe tracking
- location context

The early version should use manually created JSON or YAML files. API integrations can come later.

### 4. Story engine

Uses metadata and notes to generate a content brief.

Possible outputs:

- story angle
- title ideas
- hook
- platform captions
- thumbnail ideas
- overlay text
- editing notes

### 5. Content package generator

Produces structured outputs for different platforms.

```text
exports/
  youtube/
    title.md
    description.md
  instagram/
    caption.md
  tiktok/
    hook.md
  facebook/
    post.md
  shorts/
    caption.md
```

The first version should generate text assets and editing instructions, not final edited videos.

### 6. Editing workflow

The early system will not fully edit videos automatically.

Instead, it will prepare editing instructions and content assets for tools like:

- Insta360 App
- Insta360 Studio
- CapCut
- ChatGPT Desktop

The user should remain the final reviewer before anything is posted.

## Design principles

### Local first

The first version should work locally on macOS.

### Privacy first

Raw media, GPS data, API keys, and personal health data should not be committed to GitHub.

### Modular design

Each part of the system should be replaceable.

```text
AI provider interface
  -> ChatGPT
  -> Claude
  -> Gemini
  -> local model
```

### Human approval

The system should assist. It should not blindly publish content.

### Minimal viable automation

The project should automate the most repetitive steps first:

1. folder creation
2. file organization
3. metadata capture
4. story brief generation
5. platform text package generation

Full video automation should be treated as a later milestone.

## Initial technology direction

Possible early stack:

- Python
- Markdown
- JSON or YAML metadata
- local folder structure
- GitHub for documentation and version control
- CapCut or Insta360 tools for editing
- ChatGPT for story generation

## Future architecture ideas

- SQLite database for activity and content metadata
- Garmin or Strava API integration
- weather API integration
- local dashboard
- prompt library
- automated export package builder
- content performance analytics
