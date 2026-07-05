# Remotion content templates (v0.9)

A self-contained [Remotion](https://www.remotion.dev/) project that renders a
family of short vertical videos from synthetic, publish-safe run metadata. It
started as the v0.8 rendering prototype
([`../docs/remotion-prototype.md`](../docs/remotion-prototype.md)) and grew into a
small reusable template library in v0.9
([`../docs/remotion-templates.md`](../docs/remotion-templates.md)), satisfying
Decision 006 (evaluate Remotion as the programmable rendering layer).

Like every other tool in this repository it is **local-first** and
**privacy-first**: it makes no network calls, never publishes, and only receives
aggregate, publish-safe props (no GPS traces, no `raw/` footage, no location
context).

## Prerequisites

- Node.js 18+ and npm (this toolchain is scoped to the `remotion/` folder only;
  Python remains the pipeline's orchestration language).

## Install

```bash
cd remotion
npm install
```

## Preview

Open the Remotion Studio and edit props live:

```bash
npm run studio
# or: npx remotion studio
```

## Templates

All five compositions share the same vertical `1080x1920`, `30fps` format and the
same shared look; only the accent, duration, and props differ.

| Composition | Purpose | Sample props |
| ----------- | ------- | ------------ |
| `DailyRunShort` | One day's run recap | `src/data/sample-run.json` |
| `WeeklyTrainingRecap` | A week's training totals | `src/data/sample-week.json` |
| `RaceDaySummary` | A single race result | `src/data/sample-race.json` |
| `DataOverlayClip` | Lower-third stats bar for compositing over footage | `src/data/sample-overlay.json` |
| `ShoeReviewIntro` | Opening card for a shoe review | `src/data/sample-shoe.json` |

See [`../docs/remotion-templates.md`](../docs/remotion-templates.md) for each
template's props contract.

## Render

Render a template from its bundled synthetic props into the shared exports folder
(`exports/` is git-ignored, so the `.mp4` never enters the public repo):

```bash
npm run render:daily     # DailyRunShort   -> ../exports/shorts/daily-run-short.mp4
npm run render:weekly    # WeeklyTrainingRecap
npm run render:race      # RaceDaySummary
npm run render:overlay   # DataOverlayClip
npm run render:shoe      # ShoeReviewIntro

# or directly:
npx remotion render DailyRunShort ../exports/shorts/daily-run-short.mp4 \
  --props=src/data/sample-run.json
```

Output: vertical `1080x1920`, `30fps`, ~8-14 seconds depending on the template.
If a render fails at browser start-up with "got no response", re-run it or add
`--concurrency=1` (a transient headless-Chromium warm-up issue, not a code
problem).

## Props contract

The composition receives a small, flat subset of a validated
`content/YYYY/YYYY-MM-DD/metadata/run.json`. The field names mirror the
documented contract so `data/sample-run.json` can be passed straight through:

```json
{
  "date": "2026-07-05",
  "title": "Easy Sunday run with a strong finish",
  "distance_km": 18.2,
  "duration": "01:44:00",
  "average_pace": "5:42/km",
  "average_heart_rate": 146,
  "elevation_gain_m": 86,
  "mood": "started tired, finished strong"
}
```

Mapping from `run.json`: `title` ← `title_working`; the metric fields ←
`metrics.*`; `mood` ← `content_notes.mood`. See
[`../docs/remotion-prototype.md`](../docs/remotion-prototype.md) for the full
rationale, excluded fields, and future work.

## Structure

```text
remotion/
  package.json
  tsconfig.json
  remotion.config.ts
  src/
    index.ts                    # registerRoot entry point
    Root.tsx                    # registers every composition
    types.ts                    # publish-safe props schemas (zod)
    theme.ts                    # shared brand kit (font, gradients, accents)
    compositions/
      DailyRunShort.tsx
      WeeklyTrainingRecap.tsx
      RaceDaySummary.tsx
      DataOverlayClip.tsx
      ShoeReviewIntro.tsx
    templates/                  # shared, reusable pieces
      Background.tsx
      TitleCard.tsx
      MetricRow.tsx
      StatCallout.tsx
    data/                       # synthetic, publish-safe props per template
      sample-run.json
      sample-week.json
      sample-race.json
      sample-overlay.json
      sample-shoe.json
```
