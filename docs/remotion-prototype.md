# Remotion rendering prototype

Roadmap `v0.8`. This is a **design / options** document, written before any code
is added. It captures the goal of the Remotion prototype, the rendering options
that were considered, the option chosen and why, and the concrete shape the
prototype should take so that a later implementation can follow it directly.

Nothing here calls a network service, publishes anything, or touches private
media. The prototype must satisfy Decision 006 (evaluate Remotion as the
programmable rendering layer) and the project's local-first and privacy-first
principles by construction.

## Goal

Evaluate [Remotion](https://www.remotion.dev/) as a programmable video rendering
layer for the pipeline. Concretely, render **one** short vertical video from
synthetic run metadata and placeholder footage, displaying basic run-data
overlays, entirely on the local machine.

This closes the gap at the end of the current pipeline: today the engine produces
structured `run.json` metadata plus text packages, but the final video is still
edited by hand. A coded rendering layer turns the same validated metadata into a
repeatable video output.

```text
run.json  ->  render props  ->  Remotion composition  ->  exports/shorts/*.mp4
```

## Design principles

The prototype inherits the project-wide principles (see `docs/architecture.md`)
and Decision 006:

- **Local-first.** The render runs on macOS with a local toolchain. No cloud
  render, no upload step.
- **Privacy-first.** Only aggregate, publish-safe fields from `run.json` are
  passed as props. No GPS traces, no `raw/` footage, and no private media enter
  the public repository (Decision 004).
- **Human approval.** The prototype produces a file for review. It never
  publishes.
- **Modular.** Remotion is one replaceable rendering layer behind the metadata,
  mirroring the "AI provider interface" idea in the architecture doc. If a
  different renderer is chosen later, the `run.json` contract does not change.
- **Deterministic where possible.** Given the same props and assets, the render
  should produce the same visual output, matching how every other script in the
  repo behaves.

## Options considered

The question is how to turn structured metadata into a repeatable vertical video.

| Option | Summary | Pros | Cons |
| ------ | ------- | ---- | ---- |
| **Remotion** (React/TypeScript) | Compose videos as React components; render with a headless browser via the Remotion CLI. | Data-driven props map cleanly to `run.json`; component reuse fits the v0.9 template library; strong local-first story; large ecosystem. | Adds a Node/TypeScript toolchain alongside Python; headless-browser render is heavier than raw FFmpeg. |
| **Direct FFmpeg scripts** | Draw overlays with `drawtext`/filtergraphs and mux clips. | No new runtime beyond FFmpeg; very fast. | Overlay layout and animation are painful to express and hard to reuse as templates. |
| **MoviePy (Python)** | Stay in Python; compose clips and text programmatically. | Single language with the rest of the repo. | Weaker layout/animation model; smaller ecosystem for polished motion graphics. |
| **After Effects templates (MOGRT/`aerender`)** | Data-merge into professional templates. | High visual quality. | Proprietary, not local-first-friendly, poor fit for a public repo and CI. |
| **CapCut / Insta360 manual templates** | Continue the current manual editing tools. | No engineering. | Not programmable; does not close the automation gap. This is the status quo the prototype is meant to move beyond. |

## Decision

**Adopt Remotion for the prototype**, consistent with Decision 006.

Rationale:

- Props-in, video-out matches the existing `metadata -> ...` pipeline exactly.
- Compositions are just components, so the v0.9 template library (daily short,
  weekly recap, race day, data-overlay clip, shoe-review intro) becomes reuse of
  shared React pieces rather than five separate scripts.
- It renders locally and keeps everything in version control except the private
  media, which fits the privacy model.

Accepted trade-off: the repo gains a small Node/TypeScript toolchain scoped to
`remotion/`. Python remains the pipeline's orchestration language; the eventual
`render_template` MCP tool (v1.1) can shell out to the Remotion CLI.

## Proposed structure

A self-contained `remotion/` project at the repository root, isolated from the
Python packages:

```text
remotion/
  package.json
  tsconfig.json
  remotion.config.ts
  src/
    Root.tsx                 # registers compositions
    compositions/
      DailyRunShort.tsx      # the one prototype composition
    templates/               # shared pieces reused by v0.9 templates
      MetricRow.tsx
      TitleCard.tsx
    data/
      sample-run.json        # synthetic, publish-safe props
```

Expected render output (written into the day's export folder, matching the
existing `exports/` convention):

```text
exports/shorts/daily-run-short.mp4
```

Format: vertical `1080x1920`, `30fps`, a short duration (roughly 10-15 seconds
for the prototype).

## Data flow and props contract

The composition receives a small, flat, publish-safe subset of the validated
`content/YYYY/YYYY-MM-DD/metadata/run.json` (see `docs/metadata-schema.md`). Only
these fields cross the boundary:

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

Mapping from `run.json`:

- `title` <- `title_working`
- `distance_km`, `duration`, `average_pace`, `average_heart_rate`,
  `elevation_gain_m` <- `metrics.*`
- `mood` <- `content_notes.mood`

Explicitly **excluded** from props: anything under `conditions.location_context`,
raw clip filenames from `clips[]`, and any GPS/coordinate data (which the pipeline
never stores anyway). Placeholder footage is used in the public repo; real
`raw/` footage is only ever wired in locally.

## Render workflow (proposed)

Local commands the prototype should support once implemented:

```bash
# from the remotion/ folder
npm install

# preview in the Remotion Studio
npx remotion studio

# render the prototype from the bundled synthetic props
npx remotion render DailyRunShort ../exports/shorts/daily-run-short.mp4 \
  --props=src/data/sample-run.json
```

A later, optional Python wrapper (for example
`scripts/render_short.py --date 2026-07-05`) would read the day's `run.json`,
project it to the props contract above, and invoke the Remotion CLI. That wrapper
is out of scope for the v0.8 prototype and is noted here only to show the path
toward the v1.1 `render_template` MCP tool.

## Privacy and safety

- Only the publish-safe props listed above are passed to the renderer.
- The prototype ships with **synthetic** `sample-run.json` and placeholder
  footage only; no personal media is committed.
- `.gitignore` should keep rendered `*.mp4` outputs and any local footage out of
  version control (raw media is already excluded by Decision 004).
- No network calls and no auto-publishing, matching every other tool in the repo.

## Open questions

Decisions to confirm during implementation:

1. **Toolchain boundary** — keep `remotion/` fully separate from Python, or add a
   thin `scripts/` wrapper now? (Leaning: keep separate for v0.8.)
2. **Font and brand kit** — bundle an open-licensed font in `remotion/` for a
   consistent look across future templates.
3. **Footage source** — ship a single tiny placeholder clip vs. a solid-color
   background for the prototype.
4. **Duration/segments** — fixed length, or derive timing from `clips[]`
   durations later?
5. **CI** — should a lightweight render smoke test run in GitHub Actions, or is
   local rendering enough for the prototype stage?

## Future work

- **v0.9 Remotion content templates** — promote the shared pieces in
  `templates/` into a reusable set (daily short, weekly recap, race day summary,
  data-overlay clip, shoe-review intro), each driven by structured props.
- **v1.1 / v1.2** — expose a narrow `render_template` tool through the local MCP
  server so an AI assistant can request a render without direct file-system or
  publish access (Decision 006 initial constraints).
