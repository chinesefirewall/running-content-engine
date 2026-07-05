# AI content-notes enrichment, weather sourcing, and Apple Health import

Design for the next pipeline slice (Decision #1c from the v1.0 review: automate
the `content_notes` fields instead of typing them by hand or copy/pasting into
an AI chat window). This document specifies the design; nothing here is
implemented yet.

Resolves three open questions from the roadmap review:

1. How are `mood`, `lesson`, `story_angle`, `hook`, `key_moment`, and
   `title_working` filled in? → **`scripts/enrich_notes.py`**, a new optional
   pipeline step, calling Claude, OpenAI, or a local Ollama model.
2. How is weather sourced from the internet? → **`scripts/weather.py`**, using
   Open-Meteo (free, no API key) by city/country, with an opt-in IP-geolocation
   fallback.
3. Strava vs Apple Health? → **Apple Health export parsing now** (easy, local
   file, genuinely richer content). Strava OAuth is deferred — the existing
   Strava CSV import already covers the same aggregate metrics, and OAuth
   secret storage/refresh is exactly the "authenticated API" work Decision 006
   already deferred to the MCP milestone.

Pipeline order after this change:

```text
create_day → create_metadata → import_activity (metrics/weather/gear/health)
  → enrich_notes (NEW)
  → create_story_brief
  → create_content_package
```

`enrich_notes` sits **between** `import_activity` and `create_story_brief`
because the story brief already renders `content_notes` — today it renders the
`TODO` placeholder when those fields are empty; once `enrich_notes` has run,
it renders the AI draft instead. Nothing about `create_story_brief.py` needs
to change.

---

## 1. Weather sourcing — `scripts/weather.py`

New stdlib-only module (`urllib.request` + `json`, no new dependency), used by
`import_activity.py`.

- **Geocoding**: `https://geocoding-api.open-meteo.com/v1/search?name={city}&country={country}&count=1`
  resolves a city/country name to `(lat, lon)`. No API key required.
- **Weather**:
  - Recent dates (today, or within the last ~92 days) use the Forecast API
    (`https://api.open-meteo.com/v1/forecast`) with `past_days`, which covers
    both "today" and recent recording days.
  - Older backfilled dates fall back to the Archive API
    (`https://archive-api.open-meteo.com/v1/archive?start_date=...&end_date=...`).
  - The response's WMO `weathercode` is mapped to a short human string (e.g.
    "clear", "light rain") via a small local lookup table — no dependency
    needed, Open-Meteo publishes the code table.
- **Output**: a plain dict — `{"weather": "clear", "temperature_c": 16.4, "wind": "12 km/h"}`
  — shaped exactly like the existing `load_weather_json` return value, so it
  plugs into `import_activity.py`'s existing merge path unchanged.

### New flags on `import_activity.py`

```text
--weather-city NAME       City name to geocode, e.g. "Tallinn"
--weather-country CODE    ISO country code, e.g. "EE" (improves geocoding accuracy)
--auto-locate             Opt-in IP geolocation instead of typing a city.
                           Sends your public IP to a third-party geolocation
                           service. Never runs unless this flag is passed.
```

Precedence, consistent with the existing `--weather-file` vs `--weather` rule
(explicit CLI values always win): `--weather` / `--temperature-c` / `--wind`
> `--weather-file` > `--weather-city`/`--auto-locate` fetch.

Both `--weather-city` and `--auto-locate` are **opt-in only** — no network
call happens unless one of these flags is explicitly passed, matching the
project's local-first default. `run_day.py` gets the same flags, passed
through to the `import_activity` step.

```bash
python scripts/import_activity.py --date 2026-07-05 --weather-city Tallinn --weather-country EE
python scripts/import_activity.py --date 2026-07-05 --auto-locate
```

---

## 2. Apple Health import — `scripts/apple_health.py`

Apple Health's manual **"Export All Health Data"** (Health app → profile →
Export All Health Data) produces `export.zip` containing `export.xml`. This is
the same *local file, no OAuth, no API key* pattern as the existing
Garmin/Strava importers — the reason it's the easy win over Strava's OAuth
API.

- Recommended convention: unzip into `data/private/apple_health/export.xml`.
  Already covered by the existing `.gitignore` rule for `data/private/` — no
  gitignore change needed.
- `export.xml` is a **full multi-year history dump** (can be hundreds of MB),
  unlike the small per-activity TCX/GPX files. It must be parsed with
  `xml.etree.ElementTree.iterparse`, discarding elements outside the target
  date's window as it streams, instead of `ET.parse` (which loads the whole
  tree — fine for TCX/GPX, not fine here).
- Extracted, for the target `--date` (and, for sleep, the night before it):
  - `HKQuantityTypeIdentifierHeartRateVariabilitySDNN` → `hrv_ms`
  - `HKQuantityTypeIdentifierRestingHeartRate` → `resting_heart_rate`
  - `HKCategoryTypeIdentifierSleepAnalysis` (asleep intervals, summed) → `sleep_hours`
  - `HKQuantityTypeIdentifierVO2Max` → `vo2_max`
  - A same-day `<Workout>` of type running can also populate `metrics.*`
    exactly like the existing importers (reuses `merge_summary`), with
    `metrics.source = "apple_health"` (already a valid enum value in the
    schema today).

### New flag on `import_activity.py`

```text
--health-export PATH   Path to an Apple Health export.xml to pull HRV,
                        resting heart rate, sleep, and VO2 max from.
```

```bash
python scripts/import_activity.py --date 2026-07-05 --health-export data/private/apple_health/export.xml
```

### Schema addition — `schemas/run_metadata.schema.json`

New optional `health` object, sibling to `metrics`/`gear`/`conditions`. Purely
additive — not in `required`, so every existing `run.json` stays valid:

```json
"health": {
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "hrv_ms": {"type": ["number", "null"], "minimum": 0},
    "resting_heart_rate": {"type": ["integer", "null"], "minimum": 0},
    "sleep_hours": {"type": ["number", "null"], "minimum": 0},
    "vo2_max": {"type": ["number", "null"], "minimum": 0},
    "source": {"type": ["string", "null"], "enum": ["apple_health", "manual", null]}
  }
}
```

---

## 3. `scripts/enrich_notes.py` — the new pipeline step

Drafts `content_notes` (`mood`, `lesson`, `story_angle`, `hook`, `key_moment`)
and `title_working` from the day's metadata, using an AI provider, then merges
the result into `run.json` with the same "fill empty fields only, unless
`--overwrite`" semantics `import_activity.py` already uses.

### Provider abstraction — `scripts/ai_providers.py`

```python
class AIProvider(Protocol):
    def complete(self, prompt: str) -> str: ...

class ClaudeProvider:   # reads ANTHROPIC_API_KEY, uses the anthropic SDK
class OpenAIProvider:   # reads OPENAI_API_KEY, uses the openai SDK
class OllamaProvider:   # POSTs to http://localhost:11434/api/generate, stdlib only
```

- `get_provider(name, model=None) -> AIProvider` factory, reading env vars.
  Missing key / SDK for the chosen provider fails with a clear actionable
  message, same pattern as `create_metadata.py`'s missing-`jsonschema` error.
- **`anthropic`/`openai` are optional dependencies** (`pip install
  running-content-engine[enrich]`, or install just the one you use) — kept out
  of the core dependency list the same way `fitparse` is optional today.
  Ollama needs no SDK at all, since it's a local HTTP call.
- **Default provider is Claude** (`--provider claude`, overridable to
  `openai` or `ollama`). `--model` overrides the model id per provider.
- Important caveat to keep documented in the CLI help and README: **ChatGPT
  Plus / Claude Pro subscriptions do not include API access.** Using
  `--provider claude` or `--provider openai` requires a separate API key from
  the Anthropic Console / OpenAI Platform, billed per token (this workload is
  a few cents per run at most, but it is a different account/billing surface
  than the consumer subscriptions).

### Prompt — `prompts/enrich-content-notes.md`

A new template in the existing provider-agnostic prompt library, reusing
`create_prompt.py`'s `render_template`/`_lookup_field` machinery (no new
templating engine). It bakes in the editorial identity from
`docs/manual-review-editing-workflow.md` directly, so drafts already sound
like you instead of generic running-influencer copy:

```markdown
---
id: enrich-content-notes
title: Draft content notes from run data
description: Draft mood/lesson/story_angle/hook/key_moment/title_working for AI-assisted review.
---
You are ghostwriting short, honest running-log notes for a specific person —
not generic influencer copy. Voice: runner, data engineer, immigrant living in
Estonia, disciplined but human. Calm confidence, not fake motivation. Never use
hype phrases ("beast mode", "no pain no gain") or forced exclamation marks.
Truth beats drama: if the run was unremarkable, say so plainly instead of
inventing a dramatic arc. Never invent a stat or feeling not supported by the
data below.

Run data:
- Date: {{ date }}
- Activity: {{ activity_type }}
- Distance: {{ metrics.distance_km }} km
- Duration: {{ metrics.duration }}
- Average pace: {{ metrics.average_pace }}
- Average heart rate: {{ metrics.average_heart_rate }} bpm
- Elevation gain: {{ metrics.elevation_gain_m }} m
- Conditions: {{ conditions.weather }}, {{ conditions.temperature_c }} C, wind {{ conditions.wind }}
- Shoes: {{ gear.shoes }}
- Existing free-form notes: {{ notes_freeform }}

Return ONLY a JSON object with exactly these keys (use null for anything you
cannot honestly infer):
{"mood": ..., "lesson": ..., "story_angle": ..., "hook": ..., "key_moment": ..., "title_working": ...}
```

`health.*` fields (HRV, resting HR, sleep, VO2 max) are **excluded from this
prompt by default** when the provider is `claude` or `openai` — they are
real personal health data (NFR-002), and including them means sending them to
a third party. They're included by default only for `--provider ollama`
(fully local, nothing leaves the machine). An explicit
`--include-health-cloud` flag opts into sending `health.*` to a cloud provider
too, for anyone who wants the richer draft anyway and is fine with that
trade-off.

### Flow

1. Load `run.json` for `--date`; error out (same as `create_story_brief.py`)
   if it doesn't exist yet.
2. Render `enrich-content-notes` with the metadata (plus any free-form notes
   from `notes/*.md`, reusing `create_story_brief.read_notes`).
3. Call the selected provider's `.complete(prompt)`.
4. Parse the response as strict JSON. On a parse failure, retry once with a
   "return ONLY valid JSON" reminder; on a second failure, fail clearly and
   save the raw response to `notes/enrichment-log/<date>-<provider>.txt` for
   debugging — never silently guess at malformed output.
5. Merge into `content_notes` / `title_working`: only fill fields that are
   currently `null`, unless `--overwrite`. **`publish_intent` is never
   touched** — an AI draft never bumps publishing readiness.
6. Stamp `content_notes.draft_source` (new schema field, see below) so a
   human reviewer can see at a glance which fields were machine-drafted vs.
   typed by hand.
7. Validate against the schema and write, same as every other script.
   `--dry-run` prints the filled prompt and the parsed draft without writing;
   `--no-validate` and `--overwrite` mirror the existing scripts for
   consistency.
8. Always write an audit copy of the exact prompt sent and the raw response
   to `notes/enrichment-log/<date>-<provider>.json` — transparency for what
   left the machine, and a debugging aid.

### Schema addition — `content_notes.draft_source`

```json
"draft_source": {"type": ["string", "null"], "enum": ["manual", "ai_claude", "ai_openai", "ai_ollama", null]}
```

Optional, defaults to `null` (unset means manually written, matching every
`run.json` created before this feature existed).

### CLI

```bash
python scripts/enrich_notes.py --date 2026-07-05                          # Claude (default)
python scripts/enrich_notes.py --date 2026-07-05 --provider openai
python scripts/enrich_notes.py --date 2026-07-05 --provider ollama --model llama3.1:8b
python scripts/enrich_notes.py --date 2026-07-05 --overwrite --dry-run
```

### `run_day.py` orchestrator

New flags, all optional and off by default (mirrors how `import_activity` is
only invoked when its flags are present):

```text
--enrich                   Run the enrich_notes step.
--provider claude|openai|ollama   Default: claude.
--enrich-model NAME         Override the provider's default model.
--include-health-cloud      Opt-in: send health.* to a cloud provider too.
```

The step is skipped (idempotent, like the others) once every target
`content_notes` field is already populated, unless `--overwrite` is passed.

```bash
python scripts/run_day.py --date 2026-07-05 \
  --import-file data/sample/garmin-activity.tcx \
  --weather-city Tallinn --weather-country EE \
  --health-export data/private/apple_health/export.xml \
  --enrich --provider claude
```

---

## 4. Ollama on your hardware (Apple M2, 8GB RAM)

Recorded here since it directly shaped the "default to Claude" decision:

- 8GB unified memory realistically caps you at a **7B–8B quantized model**
  (~4.5–5GB on disk) with little headroom left for anything else running at
  the same time; a **3B–4B model** (~2–2.5GB) is snappier and leaves more
  room, at a further quality cost.
- Quality on this specific task (short, voice-matched, style-constrained
  writing) is meaningfully below Claude at every size that fits in 8GB —
  smaller local models tend toward generic, cliché-leaning phrasing and drift
  from style constraints ("no fake hype") more often.
- Since output always goes through human review before publishing, a rougher
  local draft is still a legitimate time-saver — just expect to edit local
  drafts more than Claude drafts.
- `--provider ollama` exists specifically so this can be measured on real
  days rather than guessed at.

---

## 5. New dependencies

```toml
[project.optional-dependencies]
enrich = ["anthropic>=0.40", "openai>=1.50"]
```

Ollama needs no SDK (stdlib HTTP only). Weather and Apple Health parsing need
no new dependency either (`urllib.request`, `xml.etree.ElementTree`).

## 6. New/changed files

```text
scripts/weather.py              (new)
scripts/apple_health.py         (new)
scripts/ai_providers.py         (new)
scripts/enrich_notes.py         (new)
prompts/enrich-content-notes.md (new)
schemas/run_metadata.schema.json (add health object, content_notes.draft_source)
scripts/import_activity.py      (add --weather-city/--weather-country/--auto-locate/--health-export)
scripts/run_day.py              (add --enrich/--provider/--enrich-model/--include-health-cloud pass-through)
docs/data-integration.md        (document weather sourcing + Apple Health import)
docs/roadmap.md                 (new milestone entry)
docs/decision-log.md            (new decision: cloud AI enrichment is opt-in, health data excluded from cloud prompts by default)
pyproject.toml                  (add `enrich` optional-dependencies group)
tests/test_weather.py, test_apple_health.py, test_ai_providers.py, test_enrich_notes.py (new)
.env.example                    (new: documents ANTHROPIC_API_KEY / OPENAI_API_KEY / OLLAMA_HOST)
```

## 7. Privacy summary (extends Decision 004)

- Weather and enrichment calls are **opt-in only** — no network call happens
  during a normal `run_day.py` invocation unless the relevant flags are
  passed.
- `--auto-locate` sends your public IP to a geolocation service; `--weather-city`
  sends only the city/country you type, never GPS.
- Cloud AI providers (`claude`, `openai`) receive run metrics, conditions,
  gear, and free-form notes, but **not** `health.*` unless
  `--include-health-cloud` is explicitly passed. `ollama` is fully local —
  nothing leaves the machine.
- GPS trackpoints remain never-stored, per the existing importer guarantee.