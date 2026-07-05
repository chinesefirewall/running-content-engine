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
