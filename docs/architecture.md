
---

# `docs/architecture.md`

Purpose: explain the high-level system design.

```md
# Architecture

## Overview

Running Content Engine treats content creation as a data pipeline.

The system converts raw inputs into reusable content outputs through a repeatable workflow.

```text
Camera Footage
    +
Run Data
    +
Daily Notes
    ↓
File Organization
    ↓
Metadata Layer
    ↓
Story Engine
    ↓
Content Package Generator
    ↓
Editing Workflow
    ↓
Platform Exports


Core Components
1. Media Ingestion

Responsible for importing raw video files from the action camera or phone.

Initial version may be manual.

Future version may automate file detection and copying.

2. Folder Automation

Creates a consistent daily folder structure.

Example:

content/YYYY/YYYY-MM-DD/
  raw/
  processed/
  exports/
  metadata/
  notes/
  thumbnails/
3. Metadata Collector

Stores structured information about each run.

Sources may include:

manual notes
Garmin export
Strava export
weather data
shoe tracking
location context
4. Story Engine

Uses metadata and notes to generate a content brief.

Possible outputs:

story angle
title ideas
hook
platform captions
thumbnail ideas
overlay text
5. Editing Workflow

The early system will not fully edit videos automatically.

Instead, it will prepare editing instructions and content assets for tools like:

Insta360 App
Insta360 Studio
CapCut
ChatGPT Desktop
6. Content Package Generator

Produces structured outputs for different platforms.

Example:

exports/
  youtube/
  instagram/
  tiktok/
  facebook/
  shorts/
Design Principles
Local First

The first version should work locally on a Mac.

Privacy First

Raw media, GPS data, API keys, and personal health data should not be committed to GitHub.

Modular Design

Each part of the system should be replaceable.

Example:

AI Provider Interface
  -> ChatGPT
  -> Claude
  -> Gemini
  -> Local model
Human Approval

The system should assist, not blindly publish.

The user should review outputs before posting.

Initial Technology Direction

Possible early stack:

Python
Markdown
JSON/YAML metadata
local folder structure
GitHub for documentation and version control
CapCut/Insta360 tools for editing
ChatGPT for story generation
Future Architecture Ideas
SQLite database for activity and content metadata
Garmin or Strava API integration
weather API integration
local dashboard
prompt library
automated export package builder
content performance analytics