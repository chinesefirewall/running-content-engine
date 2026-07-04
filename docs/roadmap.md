
---

# `docs/roadmap.md`

Purpose: define the phased plan.

```md
# Roadmap

## v0.1: Project Foundation

Goal: establish the project vision, documentation, folder structure, and early working approach.

Deliverables:

- README
- requirements document
- architecture document
- roadmap
- milestones
- decision log
- glossary
- first engineering journal entry

Status: in progress

## v0.2: Folder Automation

Goal: create a simple script that generates the daily content workspace.

Example command:

```bash
python scripts/create_day.py --date 2026-07-04

Expected output:

content/2026/2026-07-04/
  raw/
  processed/
  exports/
  metadata/
  notes/
  thumbnails/
v0.3: Metadata Schema

Goal: define and validate a daily run metadata file.

Example:

{
  "date": "2026-07-04",
  "activity_type": "run",
  "distance_km": 18.2,
  "average_pace": "5:42/km",
  "average_heart_rate": 146,
  "shoes": "Kiprun Kipstorm Tempo",
  "mood": "strong finish",
  "lesson": "started tired but improved after 12 km"
}
v0.4: Story Brief Generator

Goal: generate daily content ideas from metadata and notes.

Outputs:

daily story angle
YouTube title
Instagram caption
TikTok hook
Facebook post
overlay text
thumbnail ideas
v0.5: Content Package Generator

Goal: create platform-specific folders and Markdown files.

Example:

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
v0.6: AI Prompt Library

Goal: create reusable prompts for generating content.

Examples:

daily run recap
race day recap
shoe review
weekly training summary
health transformation story
v0.7: Garmin/Strava Integration

Goal: ingest activity data from exported files or APIs.

Initial approach may use manual exports.

Future approach may use authenticated APIs.

v1.0: MVP

Goal: complete a working local pipeline that supports:

daily folder creation
metadata capture
story brief generation
platform-specific content package
manual review and editing workflow
Future Ideas
automatic clip classification
transcript extraction
AI-assisted cut list
video overlay generation
publishing calendar
social media analytics
GitHub Actions for tests and documentation checks