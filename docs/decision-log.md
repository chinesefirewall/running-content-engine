# Decision Log

This file records major project decisions and the reasoning behind them.

## Decision 001: Treat content creation as a data pipeline

Date: 2026-07-04

Status: Accepted

Decision:

The project will treat running content creation as a pipeline rather than a manual editing workflow.

Reason:

The project owner is comfortable building systems and automation, but does not want to spend significant time on repetitive manual editing.

Expected benefit:

A structured pipeline should reduce friction and improve consistency over time.

Alternatives considered:

- Manual video editing only
- Using only CapCut templates
- Posting raw clips without structure

## Decision 002: Start with documentation before code

Date: 2026-07-04

Status: Accepted

Decision:

The project will begin with requirements, architecture, roadmap, milestones, and decision tracking before implementation.

Reason:

This prevents the idea from being lost in chat history and creates a professional foundation for a public portfolio project.

## Decision 003: Use GitHub for lineage tracking

Date: 2026-07-04

Status: Accepted

Decision:

The project will use branches, commits, pull requests, and documentation updates to track project evolution.

Reason:

This creates proper engineering lineage and makes the project easier to maintain over time.

## Decision 004: Keep raw media and private data out of Git

Date: 2026-07-04

Status: Accepted

Decision:

Raw videos, personal health data, GPS traces, API keys, and private exports should not be committed to the public repository.

Reason:

The repository is public and should not expose sensitive personal data.

Future action:

Add clear `.gitignore` rules and sample files that use fake data.

## Decision 005: Start with folder automation before AI editing

Date: 2026-07-04

Status: Accepted

Decision:

The first implementation milestone will be daily folder automation rather than AI editing.

Reason:

AI editing depends on a clean local workspace, consistent file naming, and structured metadata. Folder automation is the foundation that makes later automation easier and less fragile.

Alternatives considered:

- Start with AI prompts immediately
- Start with Garmin or Strava integration
- Start with video editing automation

Expected benefit:

A stable folder structure will make future media ingestion, metadata collection, story generation, and platform exports easier to implement.

## Decision 006: Evaluate Remotion as the programmable rendering layer and MCP as the AI control interface

Date: 2026-07-04

Status: Accepted for roadmap, not yet implemented

Decision:

The project will evaluate Remotion as a coded video rendering layer and a local Model Context Protocol server as the safe AI control interface for future rendering workflows.

Reason:

Remotion can turn structured metadata, clips, and templates into repeatable video outputs. MCP can expose controlled local tools to AI clients without requiring the AI assistant to freely access the whole local machine.

Expected benefit:

This creates a path toward AI-directed video generation while preserving modularity, local control, and human approval.

Initial constraints:

- Remotion should not be introduced before folder automation and metadata are stable.
- MCP tools should be narrow and safe.
- The initial MCP server should not expose delete, publish, or broad file-system access tools.
- The user should review all generated exports before publishing.

Alternatives considered:

- Use only CapCut or Insta360 templates
- Build custom FFmpeg scripts first
- Wait for fully automated AI video editors

Expected future role:

Remotion becomes the rendering engine. MCP becomes the AI-accessible control layer around safe local project actions.

## Decision 007: Complete the MVP with a pipeline orchestrator and a manual editing workflow

Date: 2026-07-05

Status: Accepted

Decision:

The v1.0 MVP is completed by two additions rather than new feature work: a thin
orchestrator, `scripts/run_day.py`, that chains the existing pipeline steps for
one recording day, and a documented human step,
`docs/manual-review-editing-workflow.md`, that defines the manual review,
editing, export settings, and pre-publish checklist.

Reason:

The individual steps (folder automation, metadata, story brief, content package,
activity import) already existed as separate scripts. The MVP gap was a single
repeatable path through them and a defined human editing step, not more code.

Expected benefit:

One command drives a whole day, re-runs are safe (idempotent, with `--dry-run`
and `--overwrite`), and the editorial identity, tooling, and publishing checklist
are captured so editing stays fast, consistent, and personal.

Alternatives considered:

- A documentation-only runbook without an orchestrator script
- A larger orchestration framework or task runner
- Leaving the steps as separate manual commands

## Decision 008: Automate content-notes drafting; prefer Apple Health over Strava OAuth

Date: 2026-07-05

Status: Accepted

Decision:

`content_notes` is now drafted by an optional AI-assisted step
(`scripts/enrich_notes.py`) that supports Claude, OpenAI, and a local Ollama
model behind one provider interface, defaulting to Claude. Cloud providers
never receive `health.*` (HRV, resting heart rate, sleep, VO2 max) unless the
caller explicitly passes `--include-health-cloud`; `ollama` gets it by
default since nothing leaves the machine. The step never touches
`publish_intent`.

Separately, of the two remaining data-source options from the v1.0 review,
Apple Health's manual `export.xml` was implemented and Strava's OAuth API was
deferred.

Reason:

Cloud AI drafting needs a decision on where personal data (metrics, mood,
health signals) is allowed to go, and the project's existing privacy
guarantees (Decision 004) don't automatically extend to a new outbound data
path -- that needed an explicit default (health data stays local unless
opted in) rather than an implicit one.

On data sources: Apple Health's export is a local file, parsed the same way
as the existing TCX/GPX importers -- no OAuth, no API keys -- and it unlocks
genuinely new content (HRV, resting heart rate, sleep) for richer mood/lesson
framing. Strava's richer fields (perceived exertion, kudos, athlete-written
titles) require Strava's OAuth API, which needs the same secret
storage/refresh work Decision 006 already deferred to the later MCP
milestone, and the existing Strava CSV import already covers the overlapping
aggregate metrics. The unequal effort-to-value ratio made this an easy call.

Expected benefit:

The `TODO: add during review` placeholders in `run.json` can now be
auto-drafted with much less manual typing or copy/pasting, while keeping the
project's privacy-first and human-approval principles: cloud calls are
opt-in, health data has its own opt-in gate, and every draft is flagged via
`content_notes.draft_source` for the human reviewer.

Alternatives considered:

- Defaulting to Ollama for privacy: rejected as the default given the user's
  8GB-RAM Apple Silicon Mac only comfortably fits 7-8B quantized models,
  which are a noticeable quality step below Claude for nuanced, style-guided
  short-form writing. Kept as a selectable `--provider ollama` option instead.
- Building Strava OAuth alongside Apple Health: rejected for this slice --
  the effort (app registration, token storage/refresh) mostly duplicates
  what the existing CSV import already provides.
- Sending all metadata including health data to cloud providers by default:
  rejected as inconsistent with Decision 004's privacy-first stance on
  personal health data specifically.

See `docs/ai-content-enrichment.md` for the full design.
