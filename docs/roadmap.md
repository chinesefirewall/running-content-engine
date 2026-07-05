# Roadmap

## v0.1: Project foundation

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

Status: complete

## v0.2: Folder automation

Goal: create a simple script that generates the daily content workspace.

Example command:

```bash
python scripts/create_day.py --date 2026-07-04
```

Expected output:

```text
content/2026/2026-07-04/
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

Status: complete

## v0.3: Metadata schema

Goal: define and validate a daily run metadata file.

Example:

```json
{
  "date": "2026-07-04",
  "activity_type": "run",
  "distance_km": 18.2,
  "average_pace": "5:42/km",
  "average_heart_rate": 146,
  "shoes": "Kiprun Kipstorm Tempo",
  "mood": "strong finish",
  "lesson": "Started tired but improved after 12 km."
}
```

Status: complete

## v0.4: Story brief generator

Goal: generate daily content ideas from metadata and notes.

Example command:

```bash
python scripts/create_story_brief.py --date 2026-07-05
```

Output: `content/2026/2026-07-05/notes/story-brief.md`

Outputs:

- daily story angle
- YouTube title
- Instagram caption
- TikTok hook
- Facebook post
- overlay text
- thumbnail ideas

Status: complete

## v0.5: Content package generator

Goal: create platform-specific folders and Markdown files.

Example command:

```bash
python scripts/create_content_package.py --date 2026-07-05
```

Example:

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
    hook.md
  thumbnails/
    ideas.md
```

Status: in progress

## v0.6: AI prompt library

Goal: create reusable prompts for generating content.

Examples:

- daily run recap
- race day recap
- shoe review
- weekly training summary
- health transformation story

## v0.7: Garmin and Strava integration

Goal: ingest activity data from exported files or APIs.

Initial approach may use manual exports.

Future approach may use authenticated APIs.

## v0.8: Remotion rendering prototype

Goal: evaluate Remotion as a programmable video rendering layer.

The prototype should render one short vertical video from synthetic metadata and placeholder footage.

Planned structure:

```text
remotion/
  src/
    compositions/
      DailyRunShort.tsx
    templates/
    data/
      sample-run.json
```

Expected output:

```text
exports/shorts/daily-run-short.mp4
```

Prototype scope:

- render a vertical daily run short
- display basic run data overlays
- use synthetic or sample metadata
- avoid real private footage in the public repository
- keep the render workflow local-first

## v0.9: Remotion content templates

Goal: create reusable coded video templates for common content types.

Possible templates:

- daily short
- weekly training recap
- race day summary
- data overlay clip
- shoe review intro

These templates should receive structured props from metadata files and produce consistent video outputs.

## v1.0: MVP

Goal: complete a working local pipeline that supports:

- daily folder creation
- metadata capture
- story brief generation
- platform-specific content package
- manual review and editing workflow

## v1.1: Local MCP server

Goal: expose safe local project tools to AI clients through a Model Context Protocol server.

Possible tools:

```text
list_days
create_daily_workspace
read_run_metadata
generate_story_brief
render_template
validate_exports
```

Initial restrictions:

- do not expose tools that delete files
- do not expose tools that publish automatically
- do not expose broad access to the user's home directory
- do not expose raw secrets, API keys, or private health data

## v1.2: AI-directed render workflow

Goal: allow an AI assistant to prepare a render plan and call safe local tools to produce platform-specific exports.

Example request:

```text
Create today's Instagram Reel from my latest run folder.
```

Expected system behavior:

1. read the daily folder
2. read metadata and notes
3. choose the correct Remotion template
4. pass render props to Remotion
5. render the video into the correct export folder
6. return a summary and output path for user review

## Future ideas

- automatic clip classification
- transcript extraction
- AI-assisted cut list
- video overlay generation
- publishing calendar
- social media analytics
- GitHub Actions for tests and documentation checks
- Remotion-based video rendering
- MCP-controlled local automation
- AI-directed multi-platform export generation
