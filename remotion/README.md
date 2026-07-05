# Remotion rendering prototype (v0.8)

A self-contained [Remotion](https://www.remotion.dev/) project that renders one
short vertical video from synthetic, publish-safe run metadata. It is the
implementation of the design in [`../docs/remotion-prototype.md`](../docs/remotion-prototype.md)
and satisfies Decision 006 (evaluate Remotion as the programmable rendering
layer).

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

## Render

Render the prototype from the bundled synthetic props into the shared exports
folder (`exports/` is git-ignored, so the `.mp4` never enters the public repo):

```bash
npm run render
# or:
npx remotion render DailyRunShort ../exports/shorts/daily-run-short.mp4 \
  --props=src/data/sample-run.json
```

Output: vertical `1080x1920`, `30fps`, ~13 seconds.

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
    index.ts                 # registerRoot entry point
    Root.tsx                 # registers compositions
    types.ts                 # publish-safe props schema
    compositions/
      DailyRunShort.tsx      # the one prototype composition
    templates/               # shared pieces reused by v0.9 templates
      MetricRow.tsx
      TitleCard.tsx
    data/
      sample-run.json        # synthetic, publish-safe props
```
