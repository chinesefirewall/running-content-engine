# Testing Playbook (Non-Technical / Newbie Friendly)

## Read this first

This is the **easiest way to try the Running Content Engine from scratch**. If you
have never touched this project (or you wrote it and forgot where it starts), this
is your entry point.

You do **not** need to understand the code. You just copy and paste commands, one
at a time, and check that you get the "Expected result" shown under each step.

**What this tool does, in one sentence:** you give it a date (and optionally your
running watch data), and it builds a neat folder for that day with a story idea and
ready-to-tweak social media captions for YouTube, Instagram, TikTok, Facebook, and
Shorts.

**What it does NOT do:** it does not edit your actual camera video, and it does not
post anything online. You stay in full control. The video editing happens by hand
later (Insta360 / CapCut) — see the very end of this guide.

### The one command that matters

If you remember nothing else, remember this. It runs the whole pipeline for one day:

```bash
python scripts/run_day.py --date today
```

Everything below just explains how to get to that command and what to do with the
result.

---

## What you need before you start

- A **Mac** (this project is built and tested for macOS).
- The project folder on your computer (the `running-content-engine` folder).
- About **20–30 minutes** the first time (mostly the one-time install).
- Your **Insta360 Ace Pro 2 run videos** (kept on your computer — never uploaded here).
- Your **Garmin activity** — you have the file `23460786710_ACTIVITY.fit`.
  - Heads up: the tool cannot read the raw `.fit` file yet. Part 2 shows the
    2-minute fix (download a `.tcx` file from Garmin instead). This is easy.

> Every command in this guide is typed into the **Terminal** app.
> To open it: press `Cmd` + `Space`, type `Terminal`, press `Enter`.

---

## Part 0 — Open the project in the Terminal

You must be "inside" the project folder before running anything.

1. Open the **Terminal** app.
2. Go into the project folder. If the project is on your Desktop in a folder called
   `Repository`, this is the command (adjust the path if yours is elsewhere):

   ```bash
   cd ~/Desktop/Repository/running-content-engine
   ```

3. Confirm you are in the right place:

   ```bash
   pwd
   ```

   **Expected result:** it prints a path that ends in `/running-content-engine`.

> Tip: You can drag the project folder from Finder onto the Terminal window right
> after typing `cd ` (with a space) — it pastes the full path for you.

---

## Part 1 — One-time setup (do this only once)

### 1.1 Check that Python is installed

```bash
python3 --version
```

**Expected result:** something like `Python 3.11.x` (or higher). Any 3.11+ is ideal;
3.10 also works for this test.

If you see `command not found`, install Python from `https://www.python.org/downloads/`
(download the macOS installer, double-click it, follow the prompts), then re-run the
check above in a **new** Terminal window.

### 1.2 Install the project

This downloads the small helpers the tool needs. Run it from inside the project
folder (Part 0):

```bash
pip install -e ".[dev]"
```

**Expected result:** a lot of text scrolls by and it ends with a line containing
`Successfully installed ...`. No red `ERROR` lines at the very end.

> If `pip` says "command not found", try `pip3 install -e ".[dev]"` instead.

### 1.3 (Optional) Check the install worked

```bash
python scripts/run_day.py --date today --dry-run
```

**Expected result:** it prints a numbered list starting with
`Mode: DRY RUN (no steps executed)` and lists steps like `create_day`,
`create_metadata`, `create_story_brief`, `create_content_package`. It does **not**
create any files (that is what "dry run" means — a safe preview).

If you see that list, your setup is working. 🎉

---

## Part 2 — Get your Garmin data in a format the tool can read

The tool reads **`.tcx`** files. Your file `23460786710_ACTIVITY.fit` is a `.fit`
file, which it cannot read yet. Getting a `.tcx` from Garmin is quick:

1. Go to `https://connect.garmin.com` in your web browser and sign in.
2. Open the **activity** (the run) you want to use.
3. Click the **gear / settings icon** (top-right of the activity page).
4. Choose **Export to TCX**.
5. Your browser downloads a file ending in `.tcx` (for example `activity.tcx`).
6. Move that `.tcx` file into the project's `data/` folder so it is easy to find,
   for example: `data/my-run.tcx`.

**Expected result:** you now have a `.tcx` file inside the project's `data/` folder.

> **No Garmin data / just want to try it?** You can skip this whole part. The project
> already ships with a sample file you can use: `data/sample/garmin-activity.tcx`.
> Or skip activity data entirely and type your distance/pace by hand later (Part 5).

> **Note the run date.** Look at when the run actually happened on Garmin. You will
> use that same date (format `YYYY-MM-DD`, e.g. `2026-07-05`) in the next step so the
> folder matches your run.

---

## Part 3 — Run the pipeline (the main event)

Pick the date of your run. In every command below, replace `2026-07-05` with your
real run date (or use the word `today`).

### Option A — With your Garmin `.tcx` file (recommended)

```bash
python scripts/run_day.py --date 2026-07-05 \
  --import-file data/my-run.tcx \
  --weather clear --temperature-c 16 --shoes "Insta360 test run"
```

(Using the built-in sample instead? Replace `data/my-run.tcx` with
`data/sample/garmin-activity.tcx`.)

### Option B — Without any activity file (type numbers by hand later)

```bash
python scripts/run_day.py --date 2026-07-05
```

**Expected result (both options):** you see progress lines like:

```text
Running daily pipeline for 2026-07-05
[run ] python scripts/create_day.py ...
[run ] python scripts/create_metadata.py ...
[run ] python scripts/create_story_brief.py ...
[run ] python scripts/create_content_package.py ...
Done. Daily pipeline complete for 2026-07-05.
```

That last line, **`Done. Daily pipeline complete ...`**, means success.

> Safe to run twice: if you run the same date again it will say `[skip] ...` for
> steps that are already done. That is normal and not an error.

### Bonus: weather and Apple Health data from the internet (optional)

Two more flags you can add to either option above, no export files needed:

```bash
# Fetch the day's weather instead of typing it (no account or key needed)
python scripts/run_day.py --date 2026-07-05 --weather-city Tallinn --weather-country EE

# Pull HRV, resting heart rate, sleep, and VO2 max from an Apple Health export
python scripts/run_day.py --date 2026-07-05 --health-export data/private/apple_health/export.xml
```

Getting the Apple Health export: on your iPhone, open **Health** → tap your
profile picture → **Export All Health Data** → AirDrop or save the resulting
`export.zip` to your Mac → unzip it → put `export.xml` at
`data/private/apple_health/export.xml` (that folder is never committed).

See `docs/data-integration.md` for details.

---

## Part 4 — Look at what was created

Everything for your run now lives in one folder:

```text
content/2026/2026-07-05/
```

To open it in Finder from the Terminal:

```bash
open content/2026/2026-07-05
```

**Expected result:** a Finder window opens showing these folders:

```text
raw/          <- you put your camera clips here (stays on your computer)
processed/
exports/      <- the ready-to-use captions live here
  youtube/
  instagram/
  tiktok/
  facebook/
  shorts/
metadata/
  run.json    <- the facts about your run
notes/
  story-brief.md   <- the story idea for the day
thumbnails/
```

The two most interesting files to open and read:

- `notes/story-brief.md` — the suggested story angle, titles, captions, and hooks.
- `metadata/run.json` — the structured facts (distance, pace, mood, lesson, etc.).

Open the story brief to read it:

```bash
open content/2026/2026-07-05/notes/story-brief.md
```

**Expected result:** a document with a story angle plus draft YouTube title,
Instagram caption, TikTok hook, Facebook post, and thumbnail ideas.

---

## Part 5 — Personalise it (make it feel like your run)

The first draft is intentionally generic. Make it yours by editing two things in
`metadata/run.json`, then regenerating.

1. Open the metadata file in a text editor (TextEdit is fine):

   ```bash
   open -e content/2026/2026-07-05/metadata/run.json
   ```

2. Fill in a few blanks (the ones that say `null`). The most impactful:
   - `"mood"` — how the run felt, e.g. `"strong finish"`.
   - `"lesson"` — one honest takeaway, e.g. `"Started tired but felt great after 3 km."`
   - If you did **not** import a Garmin file, also fill in `"distance_km"`,
     `"average_pace"`, etc. under `"metrics"`.

   Replace the word `null` with your text **in quotes**, e.g. change
   `"mood": null,` into `"mood": "strong finish",`. Keep the commas.

3. Save the file.

4. Regenerate **only the drafts** from your edited facts. Run these two commands
   (`--overwrite` refreshes the existing story brief and captions).

   > Important: do **not** use `python scripts/run_day.py --overwrite` here — that
   > would also reset `run.json` back to blanks and erase the mood/lesson you just
   > typed. Use these two targeted commands instead:

   ```bash
   python scripts/create_story_brief.py --date 2026-07-05 --overwrite
   python scripts/create_content_package.py --date 2026-07-05 --overwrite
   ```

**Expected result:** each command finishes without errors. Re-open
`notes/story-brief.md` — it now reflects your mood and lesson.

---

## Part 5b — Or let AI draft it for you (optional, needs an API key)

Instead of typing `mood`/`lesson`/`story_angle`/`hook`/`title_working` by hand
(Part 5), you can have Claude draft them from your run's actual numbers.

**One-time setup:**

1. Get an API key at `https://console.anthropic.com/settings/keys`. This is
   **not** the same as a Claude Pro subscription — Pro does not include API
   access, and this is billed separately (a few cents at most for this use).
2. Make the key available to the tool:
   ```bash
   cp .env.example .env
   ```
   Open `.env` in a text editor and paste your key after `ANTHROPIC_API_KEY=`
   (no space after the `=`). Save it.
3. Install the AI package:
   ```bash
   pip install anthropic
   ```

**Every time you want an AI draft**, load the key into your Terminal session
first, then run the script:

```bash
set -a && source .env && set +a
python scripts/enrich_notes.py --date 2026-07-05
```

**Expected result:**

```text
Updated metadata file: content/2026/2026-07-05/metadata/run.json (draft_source: ai_claude)
Audit log: content/2026/2026-07-05/notes/enrichment-log/2026-07-05-claude.json
```

Open `metadata/run.json` — `mood`, `lesson`, `story_angle`, and `hook` are now
filled in, and `content_notes.draft_source` says `"ai_claude"` so you always
know these were AI-written, not typed by hand. It never touches
`publish_intent` and never overwrites a field you already filled in by hand
(unless you add `--overwrite`).

Then regenerate the drafts exactly as in Part 5, step 4:

```bash
python scripts/create_story_brief.py --date 2026-07-05 --overwrite
python scripts/create_content_package.py --date 2026-07-05 --overwrite
```

**Read it before you trust it.** AI-drafted mood and lessons are a starting
point, not the truth — they're generated from the numbers alone, with no idea
how the run actually felt. Edit anything that doesn't match reality.

> A local, free alternative exists too (`--provider ollama`, no API key, no
> internet). It runs a smaller model on your own Mac, so expect a rougher
> draft you'll edit more. See `docs/ai-content-enrichment.md` for setup and
> the tradeoffs.

---

## Part 6 — Put your camera clips in the folder

Copy 2–3 minutes of your **Insta360 Ace Pro 2** clips into the day's `raw/` folder:

```text
content/2026/2026-07-05/raw/
```

**Expected result:** your video files sit inside `raw/`. These stay only on your
computer — they are never uploaded or shared by this tool.

---

## Part 7 — (Optional) Render a data-overlay video with code

The project can also generate a short vertical video with your run stats using a
tool called Remotion. This part is **optional** and needs **Node.js** installed.

1. If you do not have Node.js, install it first (see `remotion/README.md`; on a Mac
   the simplest route is Homebrew: `brew install node`).

2. Then run:

   ```bash
   cd remotion
   npm install
   npm run render:daily
   cd ..
   ```

**Expected result:** the first `npm install` takes a few minutes (it downloads a
mini browser — normal). `npm run render:daily` produces a `.mp4` file under the
`exports/shorts/` folder. Open it to watch the animated stats short.

> Full details, other templates (weekly, race, shoe review), and tips are in
> `remotion/README.md` and `docs/remotion-templates.md`.

---

## Part 8 — Edit the real video and publish (the human step)

This is where **you** turn the drafts and your raw clips into a finished video.
The tool has done its job; now the creative editing happens in Insta360 Studio /
CapCut.

Follow the full checklist here: **`docs/manual-review-editing-workflow.md`**.

It covers, in plain terms:
- how to review the story brief and keep it honest,
- the recommended clip structure (intro, a few run clips, a reflection),
- editing in Insta360 / CapCut and adding the Remotion overlay,
- recommended export settings per platform,
- a final pre-publish checklist.

**Expected result:** one finished vertical video plus captions you can paste into
each platform. Nothing is auto-posted — you publish manually when happy.

---

## If something goes wrong (quick fixes)

| What you see | What it means / what to do |
| --- | --- |
| `command not found: python` | Try `python3` instead of `python`. If still missing, install Python (Part 1.1). |
| `command not found: pip` | Try `pip3 install -e ".[dev]"`. |
| `No such file or directory` after a `cd` | You are not in the project folder. Redo Part 0 and check with `pwd`. |
| `Could not detect the export format ... Supported: .tcx, .gpx, .csv, .json` | You tried to import the raw `.fit` file. Use the `.tcx` from Part 2 instead. |
| `Metadata file already exists ... Use --overwrite` | The day was already created. Add `--overwrite` to refresh it (Part 5). |
| `[skip] ...` lines when running | Not an error — those steps were already done for that date. |
| The captions look generic | Expected on first run. Fill in `mood`/`lesson` by hand (Part 5) or via AI (Part 5b), then re-generate the drafts. |
| Node/`npm` errors in Part 7 | Part 7 is optional. Install Node.js first, or skip the video render entirely. |
| `ANTHROPIC_API_KEY is not set` | Part 5b's key isn't loaded into this Terminal session. Run `set -a && source .env && set +a` first. |
| `command not found: sk-ant-...` when sourcing `.env` | There's a stray space after `=` in `.env`, e.g. `ANTHROPIC_API_KEY= sk-ant-...`. Remove the space. |

If a command prints a long red error you do not understand, copy the **last few
lines** and send them to Niyi — that is usually enough to diagnose it.

---

## Command cheat sheet

```bash
# 0. Go into the project (once per Terminal window)
cd ~/Desktop/Repository/running-content-engine

# 1. One-time setup
pip install -e ".[dev]"

# 2. Safe preview (creates nothing)
python scripts/run_day.py --date today --dry-run

# 3. Run the whole day (pick your real date)
python scripts/run_day.py --date 2026-07-05

#    ...or with your Garmin TCX + weather + shoes:
python scripts/run_day.py --date 2026-07-05 \
  --import-file data/my-run.tcx \
  --weather clear --temperature-c 16 --shoes "My shoes"

#    ...or fetch weather from the internet / pull Apple Health data (Part 3 bonus):
python scripts/run_day.py --date 2026-07-05 --weather-city Tallinn --weather-country EE
python scripts/run_day.py --date 2026-07-05 --health-export data/private/apple_health/export.xml

# 4. Open the day's folder
open content/2026/2026-07-05

# 5. After editing metadata by hand, refresh ONLY the drafts
#    (do NOT use run_day --overwrite here: it would reset run.json)
python scripts/create_story_brief.py --date 2026-07-05 --overwrite
python scripts/create_content_package.py --date 2026-07-05 --overwrite

# 5b. ...or let AI draft mood/lesson/hook/title instead (Part 5b, needs an API key)
set -a && source .env && set +a
python scripts/enrich_notes.py --date 2026-07-05
python scripts/create_story_brief.py --date 2026-07-05 --overwrite
python scripts/create_content_package.py --date 2026-07-05 --overwrite

# 6. (Optional) render a stats video
cd remotion && npm install && npm run render:daily && cd ..
```

---

## Feedback checklist for the tester

Please tell Niyi:

1. Did the one-time setup (`pip install`) finish without errors? (yes / no + the error)
2. Did `python scripts/run_day.py --date <date>` end with `Done. Daily pipeline complete`?
3. Were you able to get a `.tcx` from Garmin and import it? Any confusion?
4. After editing `mood`/`lesson` and re-running, did the story brief improve?
5. Did the captions in `exports/` feel usable, or too generic?
6. (If tried) did the Remotion video render? How long did it take?
7. (If tried) did the AI-drafted content notes (Part 5b) feel accurate and in
   your voice, or did you have to rewrite most of it?
8. Where did you get stuck, confused, or lost? (This is the most useful feedback.)
9. Overall: could you follow this guide without asking for help? (1 = not at all,
   5 = totally smooth)
