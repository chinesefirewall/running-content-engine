# Manual Review and Editing Workflow

## Purpose

This document defines the human review and editing step in the Running Content
Engine. It is the last missing MVP piece: the pipeline can generate the daily
folder, metadata, story brief, and platform content drafts, but the editor still
decides what is true, what is worth publishing, and what should be cut.

The system produces the draft. The human keeps editorial control.

The goal is to make editing fast, repeatable, and personal.

## Editorial identity

The content should feel like:

- runner
- data engineer
- health transformation
- Nigerian living in Estonia
- curious learner
- disciplined but honest
- technical, but not robotic
- calm confidence, not fake motivation

The tone is bold, direct, and reflective.

Preferred style:

```text
I ran the data.
I ran the miles.
The lesson was not in the pace. It was in showing up.
```

Avoid:

- fake hype
- overused motivational speeches
- pretending every run is life-changing
- copying generic fitness influencer language
- excessive filters or dramatic edits

## Core principle

Record once. Reuse many times.

One recording session should produce:

- one main short video
- one platform caption set
- optional still frames
- optional data overlay
- optional longer reflection for YouTube or Facebook

## The time budget

The biggest risk is not poor camera quality. It is making the editing workflow
so heavy that it stops happening. The workflow is built around one rule:

> Maximum 20 minutes for normal daily content. Maximum 45 minutes for long runs
> or race days.

If a step does not fit the budget, cut it.

## Where this fits in the pipeline

The automated steps run first (see `README.md` and `scripts/run_day.py`):

```text
scripts/run_day.py --date YYYY-MM-DD
  -> content/YYYY/YYYY-MM-DD/metadata/run.json
  -> content/YYYY/YYYY-MM-DD/notes/story-brief.md
  -> content/YYYY/YYYY-MM-DD/exports/{youtube,instagram,tiktok,facebook,shorts}/...
```

This manual step then turns those drafts and the raw clips into a finished,
publish-ready video:

```text
Review story
  -> choose one angle
  -> edit clips
  -> add overlays and captions
  -> export platform versions
  -> final human check
```

## Standard daily clip structure

For a normal run, record only:

1. Morning intro, about 30 seconds
2. Run clip 1, about 10 to 15 seconds
3. Run clip 2, about 10 to 15 seconds
4. Run clip 3, about 10 to 15 seconds
5. Finish reflection, about 45 to 60 seconds

Total raw footage target: 2 to 3 minutes. This keeps editing realistic.

## Review loop

### Step 1: Read the generated story brief

Open:

```text
content/YYYY/YYYY-MM-DD/notes/story-brief.md
```

Check:

- Is the story true?
- Is the angle interesting?
- Does it match how the run actually felt?
- Is there anything too private to publish?
- Is the hook strong enough?

If the story brief feels exaggerated, rewrite it. Truth beats drama.

### Step 2: Review the metadata

Open:

```text
content/YYYY/YYYY-MM-DD/metadata/run.json
```

Check distance, pace, heart rate, shoes, weather, mood, lesson, story angle, and
`publish_intent`. Do not publish exact GPS traces or sensitive health details.

### Step 3: Choose one story angle

Pick only one. Examples:

```text
Low energy, still showed up.
Strong finish after a slow start.
Easy run became a mental reset.
The data said easy, the body said otherwise.
Building consistency before confidence.
```

Do not try to tell five stories in one short video.

### Step 4: Choose the edit type

Pick the edit type that matches the run. Each maps to a Remotion template where a
programmable graphic helps (see `docs/remotion-templates.md`).

#### Daily Log

Best for normal easy runs.

```text
Intro -> 2 running clips -> finish reflection -> data overlay
```

Length: 30 to 60 seconds.

#### Data Run

Best when the metrics are interesting.

```text
Hook -> Garmin/Strava metrics -> running clips -> lesson
```

Length: 45 to 75 seconds.

#### Long Run Mini Documentary

Best for weekend long runs.

```text
Before -> early struggle -> middle section -> final kilometres -> reflection
```

Length: 90 seconds to 3 minutes.

#### Race Day

Best for events.

```text
Pre-race -> atmosphere -> key moments -> finish -> result -> lesson
```

Length: 1 to 5 minutes.

#### Tech Runner

Best for data-engineering style content.

```text
Problem -> data -> experiment -> result -> lesson
```

Example:

```text
Problem: My easy runs are becoming too fast.
Data: Avg HR has been rising.
Experiment: Keep today under 145 bpm.
Result: 12 km controlled.
Lesson: The body gives better feedback than ego.
```

## Editing tool workflow

### Insta360 app

Use for a quick AI-assisted first draft, auto highlight selection, basic
stabilization, and fast mobile edits. Best for daily runs, quick reels, and
low-effort drafts.

### CapCut

Use for captions, music, final trimming, platform-specific formatting, and
TikTok/Reels/Shorts exports. Best for final social polish and short-form
formatting.

### Remotion

Use for data overlays, intro templates, weekly recap graphics, charts, and other
repeatable video components. Remotion is not the main editor; it is the
programmable graphics layer. See `remotion/README.md` and
`docs/remotion-templates.md`.

## Recommended editing workflow

### Normal daily run (target 15 to 20 minutes)

```text
1. Open notes/story-brief.md
2. Pick one story angle
3. Import clips into Insta360 app or CapCut
4. Create a 30 to 60 second edit
5. Add captions
6. Add 1 to 3 data overlays
7. Export the vertical version
8. Review once
9. Save into the day's exports/ folder
```

### Long run or race day (target 30 to 45 minutes)

```text
1. Read metadata/run.json
2. Read notes/story-brief.md
3. Choose the edit type
4. Select the best clips manually
5. Create the longer edit
6. Add captions
7. Add data overlays
8. Add one reflective quote or lesson
9. Export vertical and horizontal versions
10. Review before publishing
```

## Recommended export settings

Keep exports simple and consistent so they are predictable across platforms.

| Use | Aspect ratio | Resolution | Frame rate | Notes |
|---|---|---|---|---|
| Shorts / Reels / TikTok | 9:16 (vertical) | 1080x1920 | 30 fps | Primary daily format; matches the Remotion templates |
| YouTube long-form | 16:9 (horizontal) | 1920x1080 | 30 fps | Race days and mini documentaries |
| Still frames / thumbnails | 9:16 or 16:9 | 1080x1920 / 1920x1080 | n/a | Export a clean frame for the thumbnail idea |

Codec: H.264 MP4, high bitrate, captions burned in for silent viewing.

## Data overlay style

The content should visually show that the creator is a data engineer. Use
overlays that read like field names, logs, or metrics.

```text
Distance: 18.2 km
Avg Pace: 5:42/km
Avg HR: 146 bpm
Shoes: Kipstorm Tempo
Condition: Cloudy, 17C
Lesson: Strong finish after 12 km
```

```text
run.status = completed
effort_level = controlled
lesson = consistency beats mood
```

Use these carefully. The tech style should be fun, not forced.

## Visual style

- clean captions
- simple data overlays
- strong contrast
- minimal clutter
- occasional code-style text
- no excessive transitions
- no chaotic effects

The viewer should feel: this person is technical, disciplined, and real.

## Caption style

Captions should be short, direct, and reflective.

Good examples:

```text
I did not feel ready today. Still ran.
The pace was not special. The consistency was.
Some days the win is not speed. It is execution.
Data says easy run. Ego says prove something. Today, data won.
Another quiet deposit into the fitness account.
```

Avoid:

```text
No pain no gain!!!
Beast mode activated!!!
Nobody can stop me!!!
```

## Platform-specific review

### YouTube

- Is the title clear?
- Do the first 5 seconds explain why this matters?
- Is the description useful?
- Is there a thumbnail idea?
- Is it better as a Short or a longer upload?

### Instagram

- Is the first line strong?
- Are captions readable without sound?
- Does it feel visually clean and personal enough?

### TikTok

- Is the hook immediate?
- Is the video too slow?
- Is the lesson clear by the end?
- Can a stranger understand it without context?

### Facebook

- Is it friendly for old friends, schoolmates, work friends, and family?
- Is it not too technical?
- Is it honest without oversharing?

### LinkedIn (optional)

Use only when there is a genuine work-life, discipline, systems, health, or data
angle. Do not turn every run into career content.

## Publishing decision

Before posting, set the metadata `publish_intent` to one of:

```text
do_not_publish
draft
ready_for_review
published
```

The default is `do_not_publish`. Only move to `ready_for_review` when:

- no sensitive information is exposed
- captions are clean
- the story is true
- the video is watchable without sound
- export quality is acceptable

## Final human review checklist

Before publishing, confirm:

- [ ] The story is true.
- [ ] No exact private location is visible.
- [ ] No private health or legal detail is exposed.
- [ ] Captions are readable.
- [ ] Audio is understandable.
- [ ] Data overlays are accurate.
- [ ] The hook is clear in the first 3 seconds.
- [ ] The video has one main idea.
- [ ] The ending gives a lesson, result, or feeling.
- [ ] The platform caption matches the video.

## Definition of done

A daily content package is complete when:

```text
metadata/run.json exists
notes/story-brief.md exists
exports/* text assets exist
at least one edited video is exported
the final review checklist is completed
publish_intent is updated
```

## Guiding rule

Make it good enough to publish, not perfect enough to delay. The goal is
consistency, not cinema.
