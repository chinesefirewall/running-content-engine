# Remotion content templates

Roadmap `v0.9`. This builds directly on the v0.8 rendering prototype
(`docs/remotion-prototype.md`) and promotes its two shared pieces
(`TitleCard`, `MetricRow`) into a small **reusable template library**. Each
template is a Remotion composition that receives structured, publish-safe props
and renders a consistent vertical short.

Like the prototype, everything here is **local-first** and **privacy-first**
(Decision 004 / Decision 006): no network calls, no auto-publishing, and only
aggregate, publish-safe fields ever reach a template (no GPS traces, no `raw/`
footage, no location context).

## Goal

Turn the one-off daily short into a family of coded templates for the common
content types the channel produces, so a new video is "pick a template, pass
props" rather than a bespoke edit each time.

```text
metadata  ->  props (per template)  ->  Remotion composition  ->  exports/shorts/*.mp4
```

## Templates

All five compositions share the same vertical `1080x1920`, `30fps` format and the
same shared look; only the accent colour, duration, and props differ.

| Composition | Purpose | Lead element | Sample props |
| ----------- | ------- | ------------ | ------------ |
| `DailyRunShort` | One day's run recap (from v0.8) | Title + metric list | `src/data/sample-run.json` |
| `WeeklyTrainingRecap` | A week's training totals | Total distance hero stat | `src/data/sample-week.json` |
| `RaceDaySummary` | A single race result | Finish time hero stat | `src/data/sample-race.json` |
| `DataOverlayClip` | Lower-third stats bar for compositing over footage | Bottom stats panel | `src/data/sample-overlay.json` |
| `ShoeReviewIntro` | Opening card for a shoe review | Distance-on-shoe hero stat | `src/data/sample-shoe.json` |

## Shared building blocks

The library keeps the look consistent by sharing a handful of small pieces under
`remotion/src/`:

- `theme.ts` — the brand kit: the shared font, one gradient per content type, and
  one accent colour per content type. A re-brand is a single-file change.
- `templates/Background.tsx` — the gradient background wrapper: applies the font,
  consistent padding, and a gentle fade-out over the last half second. Templates
  drop their content in as children.
- `templates/TitleCard.tsx` — an uppercase eyebrow (date / week / label) above a
  large title, themeable via an `accent` prop.
- `templates/MetricRow.tsx` — a single label-plus-value row that staggers in via
  a per-row `delay`.
- `templates/StatCallout.tsx` — a large hero number with a caption, for templates
  that lead with one headline figure.

Every template composes these, so adding a sixth template later is mostly a new
composition file plus a schema and sample props.

## Props contracts

Each template owns its own small, flat, publish-safe schema in
`remotion/src/types.ts` (validated with `zod`). Field names mirror aggregate
metadata so the bundled sample JSON can be passed straight through with
`--props`.

### `WeeklyTrainingRecap`

```json
{
  "week_of": "Jun 29 – Jul 5, 2026",
  "title": "Weekly training recap",
  "total_distance_km": 62.4,
  "total_duration": "05:38:00",
  "runs": 5,
  "total_elevation_gain_m": 410,
  "best_pace": "4:58/km",
  "summary": "Consistent week capped by a strong long run."
}
```

These map to weekly aggregates of `metrics.*` across a week's `run.json` files.

### `RaceDaySummary`

```json
{
  "date": "2026-06-14",
  "race_name": "Sample City Half Marathon",
  "distance_km": 21.1,
  "finish_time": "01:38:42",
  "average_pace": "4:41/km",
  "placement": "Top 15%",
  "highlight": "Negative split with a strong final 5 km."
}
```

`race_name`/`highlight` come from `title_working`/`content_notes.*`; the rest from
`metrics.*`. `placement` is a free string so nothing personal is required.

### `DataOverlayClip`

```json
{
  "date": "2026-07-05",
  "title": "Sunday long run",
  "distance_km": 18.2,
  "average_pace": "5:42/km",
  "average_heart_rate": 146
}
```

A deliberately minimal subset of the daily metrics. In the public repo it renders
over the shared placeholder gradient; locally it can be rendered with an alpha
channel (a codec that supports transparency) and composited over real `raw/`
footage.

### `ShoeReviewIntro`

```json
{
  "shoe_name": "Sample Racer Pro 2",
  "category": "Race day super shoe",
  "total_distance_km": 320,
  "rating": "4.5 / 5",
  "verdict": "Fast, springy, and still going strong."
}
```

`shoe_name` maps to `gear.shoes`; `total_distance_km` is the accumulated distance
on that pair; `category`/`rating`/`verdict` are review copy. `rating` is a free
string so the template stays presentation-only.

## Render workflow

From the `remotion/` folder (see `remotion/README.md` for setup):

```bash
npm install

# preview all templates in the Studio
npm run studio

# render an individual template into the shared exports folder
npm run render:daily
npm run render:weekly
npm run render:race
npm run render:overlay
npm run render:shoe
```

`exports/` is git-ignored, so the rendered `*.mp4` files never enter the public
repo. If a render fails at browser start-up with "got no response", re-run it or
add `--concurrency=1` (a transient headless-Chromium warm-up issue, not a code
problem).

## Privacy and safety

- Only the publish-safe props listed above are passed to any template.
- All templates ship with **synthetic** sample props and a solid-gradient
  background only; no personal media is committed.
- No network calls and no auto-publishing, matching every other tool in the repo.

## Future work

- A thin Python wrapper (for example `scripts/render_short.py --template weekly
  --date ...`) that reads `run.json` (or a week of them), projects it to the
  right props contract, and invokes the Remotion CLI — the path toward the v1.1
  `render_template` MCP tool (Decision 006).
- An open-licensed bundled font for a fully deterministic look across machines.
- Deriving clip timing/segments from `clips[]` durations for footage-backed
  templates.
