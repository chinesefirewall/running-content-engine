# Data integration (Garmin & Strava)

Roadmap `v0.7` / Milestone 6. The activity importer fills a day's run metadata
from a **local exported file** so run metrics no longer have to be typed by hand.
It enriches the same `content/YYYY/YYYY-MM-DD/metadata/run.json` that the entire
pipeline already consumes (`metadata → story brief → content package → prompts`).

The importer is `scripts/import_activity.py`. Like every other script in this
repository it is **deterministic and local-first**: it makes no network calls,
never publishes anything, and validates metadata against
`schemas/run_metadata.schema.json` before writing.

## Privacy guarantees

This tool is built to satisfy Decision 004 (privacy-first) by construction:

- Only **aggregate summary metrics** ever reach `run.json` (distance, duration,
  average pace, average/max heart rate, elevation gain, calories, and the source).
- **GPS trackpoints are never stored.** Latitude/longitude are read transiently
  only to compute total distance (GPX) and are then discarded. No coordinate,
  trackpoint, or route data is written anywhere.
- Raw exports stay out of version control. Keep them under a git-ignored path
  such as `data/raw/` or `data/private/` (both are already git-ignored, as are
  `*.fit`, `*.gpx`, and `*.tcx` files).

## Supported formats

Format is auto-detected by extension and, if needed, by content:

| Format | Extension | Source data used |
| ------ | --------- | ---------------- |
| Garmin TCX | `.tcx` | lap distance/time/calories, lap avg & max HR, trackpoint altitude for elevation gain |
| GPX | `.gpx` | haversine distance from trackpoints, first/last time for duration, `ele` for elevation gain, `hr` extension for heart rate |
| Strava CSV | `.csv` | one activity row selected by `--date` |
| Activity JSON | `.json` | flexible key names (`distance_km`/`distance_meters`, `moving_time`, `average_heart_rate`, `total_elevation_gain`, `calories`, `source`) |

Only the standard library is used to parse these (`xml.etree.ElementTree`, `csv`,
`json`) — no new dependencies. Binary `.fit` parsing is intentionally **deferred**
(it needs a third-party library) and is documented as future work.

## Usage

Populate a day's metrics from an export (the metadata file is created from the
starter if it does not exist yet, otherwise it is merged in place):

```bash
python scripts/import_activity.py --file data/sample/garmin-activity.tcx --date 2026-07-05
```

Strava CSV exports can contain many activities — the row is selected by `--date`:

```bash
python scripts/import_activity.py --file data/sample/strava-activities.csv --date 2026-07-05
```

Record the day's weather and gear without any data export:

```bash
python scripts/import_activity.py --date 2026-07-05 \
  --weather clear --temperature-c 16 --wind calm \
  --shoes "Sample Trainer 5" --watch "Sample Watch 2"
```

Preview the merged metadata without writing it:

```bash
python scripts/import_activity.py --file data/sample/activity.gpx --date 2026-07-05 --dry-run
```

### Flags

- `--file` — path to the local export. Optional when only recording weather/gear.
- `--date` — recording date (`YYYY-MM-DD` or `today`). Required. Also selects the
  Strava CSV row.
- `--root` — content workspace root (default `content`).
- `--metadata` — explicit path to the `run.json` file (overrides the default).
- `--source` — override the recorded `metrics.source`
  (`manual|garmin|strava|apple_health|other`).
- `--weather`, `--temperature-c`, `--wind` — weather enrichment.
- `--weather-file` — a local JSON file with `weather`/`temperature_c`/`wind`
  (CLI flags take precedence over the file).
- `--shoes`, `--watch` — gear enrichment.
- `--shoe-registry` — optional local JSON file mapping shoe aliases to full names
  (see below).
- `--overwrite` — replace already-populated fields (by default existing values
  are preserved and only empty fields are filled).
- `--dry-run` — print the merged metadata and write nothing.
- `--no-validate` — skip schema validation (not recommended).

## Merge semantics

The importer **merges** into the existing `run.json`:

- Only the fields the export actually provides are considered.
- Existing populated values are preserved unless `--overwrite` is given.
- `metrics.source` is upgraded from the default `manual` to the detected source.
- Unrelated fields (notes, other gear, clips) are always left untouched.
- `updated_at` is refreshed whenever something changes.

## Optional shoe registry

To keep shoe names consistent you can maintain a small git-ignored JSON file that
maps short aliases to full names, for example `data/private/shoes.json`:

```json
{
  "daily": "Sample Trainer 5",
  "race": "Sample Racer Pro"
}
```

Then pass an alias and the registry path:

```bash
python scripts/import_activity.py --date 2026-07-05 --shoes daily \
  --shoe-registry data/private/shoes.json
```

If no registry is given, or the alias is not found, the value you pass is used
verbatim.

## Sample fixtures

Privacy-safe sample exports with **fake data only** live under `data/sample/`:
`garmin-activity.tcx`, `activity.gpx`, `strava-activities.csv`, and
`activity.json`. They are used by the tests and are safe to keep in version
control.

## Future work

- Binary `.fit` parsing behind an optional dependency (documented in
  `pyproject.toml`).
- Authenticated Garmin/Strava API access (OAuth/secrets), deferred to the later
  MCP milestone per Decision 006 so no secrets enter the repository.
