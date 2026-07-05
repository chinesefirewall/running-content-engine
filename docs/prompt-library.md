# Prompt Library

## Purpose

The prompt library is a set of reusable, version-controlled prompt templates for
turning a day's run metadata into content ideas with an AI tool of your choice.

It is the raw material a human (and, later, the MCP layer) uses to generate
captions, hooks, titles, and descriptions. Keeping the prompts in the repository
means they can be reviewed, improved, and reused over time.

The renderer is deterministic and local-first: it does not call any external AI
service and never publishes anything. It fills a template with metadata and
writes a ready-to-paste prompt; the human pastes it into ChatGPT, Claude,
Gemini, or a local model.

## Template location

The templates live at the repository root so they are version-controlled and
provider-agnostic:

```text
prompts/
  daily-run-recap.md
  race-day-recap.md
  shoe-review.md
  weekly-training-summary.md
  health-transformation-story.md
```

Each template has light YAML front matter and a Markdown body with
`{{ dotted.path }}` tokens that map to fields in `run.json`:

```markdown
---
id: daily-run-recap
title: Daily run recap
platforms: [youtube, instagram, tiktok, facebook, shorts]
required_fields: [date, activity_type, metrics.distance_km]
---
Run data:
- Date: {{ date }}
- Distance: {{ metrics.distance_km }} km
- Mood: {{ content_notes.mood }}
```

## Output location

For each daily workspace, filled prompts are written to:

```text
content/YYYY/YYYY-MM-DD/notes/prompts/<prompt-id>.md
```

## Listing available prompts

```bash
python scripts/create_prompt.py --list
```

## Generating a filled prompt

Fill a template with a day's metadata:

```bash
python scripts/create_prompt.py --prompt daily-run-recap --date 2026-07-05
```

Preview without writing:

```bash
python scripts/create_prompt.py --prompt daily-run-recap --date 2026-07-05 --dry-run
```

Overwrite an existing filled prompt:

```bash
python scripts/create_prompt.py --prompt daily-run-recap --date 2026-07-05 --overwrite
```

Use an explicit metadata file:

```bash
python scripts/create_prompt.py --prompt shoe-review --date 2026-07-05 --metadata path/to/run.json
```

The run metadata is validated against `schemas/run_metadata.schema.json` before
the prompt is generated. Skip validation (not recommended) with `--no-validate`.

Fields that are missing from the metadata are filled with a `TODO` placeholder
so it is clear what still needs a human touch.

## Adding a new template

1. Add a new Markdown file under `prompts/` with a unique `id` in its front
   matter.
2. Use `{{ dotted.path }}` tokens for any `run.json` fields you want filled in.
3. Run `python scripts/create_prompt.py --list` to confirm it is discovered.

No code change is needed; templates are discovered automatically.

## Manual review

The filled prompt is a starting point, not a finished post. Review it, paste it
into your AI tool, and then review the AI's output for accuracy and privacy
before using any of it. Nothing is published automatically.
