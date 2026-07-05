# Content Package

## Purpose

A content package turns a day's run metadata (`run.json`) into platform-specific,
ready-to-use Markdown files, written into the day's `exports/` folders.

It is the step after the story brief: the story brief explores content ideas,
while the content package produces one concrete draft file per platform surface.

The generator is deterministic and local-first: it does not call any external
AI service and never publishes anything. Every file is a draft meant to be
reviewed and refined by a human before use.

## File locations

For each daily workspace, the generator writes:

```text
content/YYYY/YYYY-MM-DD/
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

## Inputs

The generator reads:

- `content/YYYY/YYYY-MM-DD/metadata/run.json` (validated against the schema)

## Generating a content package

Create a content package for a day:

```bash
python scripts/create_content_package.py --date 2026-07-05
```

Preview without writing:

```bash
python scripts/create_content_package.py --date 2026-07-05 --dry-run
```

Overwrite existing package files:

```bash
python scripts/create_content_package.py --date 2026-07-05 --overwrite
```

Use an explicit metadata file:

```bash
python scripts/create_content_package.py --date 2026-07-05 --metadata path/to/run.json
```

The run metadata is validated against `schemas/run_metadata.schema.json` before
the package is generated. Skip validation (not recommended) with `--no-validate`.

## Output files

| File | Platform surface |
| --- | --- |
| `exports/youtube/title.md` | YouTube title options |
| `exports/youtube/description.md` | YouTube description |
| `exports/instagram/caption.md` | Instagram caption |
| `exports/tiktok/hook.md` | TikTok hook |
| `exports/facebook/post.md` | Facebook post |
| `exports/shorts/hook.md` | YouTube Shorts hook |
| `thumbnails/ideas.md` | Thumbnail ideas |

Fields that are missing from the metadata are filled with a `TODO` placeholder
so it is clear what still needs a human touch.

## Manual review

Nothing is published automatically. By default the generator refuses to
overwrite existing files, so reviewed edits are never lost. Confirm accuracy and
privacy before using any of the generated text.
