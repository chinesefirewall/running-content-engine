# Requirements

## Project Goal

Running Content Engine is an AI-assisted pipeline for turning running footage, training data, and daily notes into reusable social media content packages.

The system should reduce the manual effort required to create running-related content while preserving the user's authentic voice and personal story.

## Primary User

The first user is the project owner: a runner, data engineer, and content beginner who wants to document daily training, health transformation, and life in Estonia.

## Core Problem

Manual video editing is repetitive and time-consuming. The goal is to build a repeatable workflow where one recording session can produce multiple outputs for different platforms.

## Functional Requirements

### FR-001: Folder Organization

The system should create a consistent folder structure for each recording day.

Example:

```text
content/
  2026/
    2026-07-04/
      raw/
      processed/
      exports/
      metadata/
      notes/
      thumbnails/

FR-002: File Naming

The system should support consistent naming of imported video files.

Example:

2026-07-04_morning_intro_001.mp4
2026-07-04_run_clip_001.mp4
2026-07-04_finish_reflection_001.mp4
FR-003: Metadata Capture

The system should store structured metadata for each run.

Possible metadata:

date
distance
duration
average pace
average heart rate
elevation gain
shoe used
weather
location context
mood
lesson of the day
FR-004: Story Brief Generation

The system should generate a daily story brief from run data and user notes.

FR-005: Multi-Platform Content Package

The system should generate platform-specific content assets.

Target platforms:

YouTube
YouTube Shorts
Instagram Reels
TikTok
Facebook
LinkedIn, optional
FR-006: AI-Assisted Captions and Hooks

The system should generate:

titles
hooks
captions
hashtags
thumbnail text
video descriptions
suggested overlay text
FR-007: Editing Support

The system should support AI-assisted editing workflows, even if final video editing remains semi-manual.

Possible tools:

Insta360 App
Insta360 Studio
CapCut
ChatGPT
future video automation tools
Non-Functional Requirements
NFR-001: Low Friction

The workflow must be simple enough to use after a run with low mental effort.

NFR-002: Privacy First

The project must avoid committing private health data, GPS traces, raw videos, API tokens, or personal files to the public repository.

NFR-003: Portability

The system should be designed so components can be swapped later.

Example:

Garmin can be replaced with Strava
Insta360 can be replaced with DJI
ChatGPT can be replaced with another AI provider
NFR-004: Local First

The early version should run locally on macOS.

NFR-005: Git-Friendly

Configuration, metadata schemas, prompts, and documentation should be version-controlled.

Raw media files should not be committed.

Out of Scope for v0.1
fully automatic video editing
automatic publishing to social media
production-grade Garmin or Strava API integration
cloud deployment
mobile app
analytics dashboard
Success Criteria for v0.1

The project is successful at v0.1 if it has:

clear documentation
clear folder structure
initial requirements
initial architecture
roadmap
decision log
milestone structure