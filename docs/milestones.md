# Milestones

## Milestone 0: Repository setup

Status: complete

Objective:

Create a clean public repository with professional documentation structure.

Checklist:

- [x] Create GitHub repository
- [x] Create feature branch
- [x] Add documentation folders
- [x] Remove local IDE files from Git tracking
- [x] Populate planning documents
- [x] Open first pull request
- [x] Merge to main

## Milestone 1: Daily folder structure

Status: complete

Objective:

Create a repeatable local folder structure for each recording day.

Checklist:

- [x] Define folder naming convention
- [x] Create folder automation script
- [x] Add dry-run mode
- [x] Add basic tests
- [x] Document usage
- [x] Open pull request
- [x] Merge to main

## Milestone 2: Run metadata standard

Status: complete

Objective:

Create a structured metadata format for daily runs.

Checklist:

- [x] Define metadata fields
- [x] Choose JSON or YAML
- [x] Create sample metadata file
- [x] Add starter metadata generator
- [x] Validate generated metadata against the JSON schema
- [x] Add basic tests
- [x] Document required and optional fields
- [x] Open pull request
- [x] Merge to main

## Milestone 3: Story brief generator

Status: complete

Objective:

Generate a daily story brief from notes and metadata.

Checklist:

- [x] Define story brief template
- [x] Create initial AI prompt (delivered by the roadmap v0.6 prompt library; see docs/prompt-library.md)
- [x] Generate sample output
- [x] Add manual review step
- [x] Save generated output to daily folder
- [x] Open pull request
- [x] Merge to main

## Milestone 4: Platform content package

Status: complete

Objective:

Generate reusable content assets for multiple platforms.

Checklist:

- [x] YouTube package
- [x] Instagram package
- [x] TikTok package
- [x] Facebook package
- [x] YouTube Shorts package
- [x] Thumbnail ideas
- [x] Open pull request
- [x] Merge to main

## Milestone 5: Editing workflow integration

Status: complete

Objective:

Support a low-effort editing workflow using external tools.

Delivered by `docs/manual-review-editing-workflow.md`, which defines the manual
review loop, editing tool workflow, recommended export settings, and the
pre-publish checklist.

Checklist:

- [x] Document Insta360 workflow
- [x] Document CapCut workflow
- [x] Create recommended export settings
- [x] Create manual editing checklist
- [x] Explore AI editing options

## Milestone 6: Data integration

Status: in progress

Objective:

Bring in Garmin, Strava, weather, and shoe data.

Delivered by the roadmap v0.7 importer (`scripts/import_activity.py`); see
`docs/data-integration.md`.

Checklist:

- [x] Manual Garmin export support
- [x] Manual Strava export support
- [x] Weather metadata support
- [x] Shoe tracking support
- [ ] Evaluate API integration
- [ ] Open pull request
- [ ] Merge to main

## Milestone 7: MVP

Status: complete

Objective:

A complete local workflow from recording day to content package.

The automated steps are chained by `scripts/run_day.py`, and the manual review,
editing, and export step is defined in
`docs/manual-review-editing-workflow.md`. See the README "End-to-end runbook
(MVP)" section for the full one-day flow.

Checklist:

- [x] Create daily folder
- [x] Import or place raw clips
- [x] Add run metadata
- [x] Generate story brief
- [x] Generate platform assets
- [x] Edit manually or semi-automatically
- [x] Export final files
