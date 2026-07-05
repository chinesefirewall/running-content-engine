import {z} from 'zod';

// The publish-safe props contract for the prototype. This is a small, flat
// subset of the validated `content/YYYY/YYYY-MM-DD/metadata/run.json`
// (see docs/metadata-schema.md and docs/remotion-prototype.md).
//
// Field names deliberately mirror the documented contract (snake_case) so the
// bundled `data/sample-run.json` can be passed straight through with
// `--props`. Only aggregate, publish-safe fields cross this boundary: no GPS
// traces, no raw clip filenames, and no location context (Decision 004).
export const dailyRunShortSchema = z.object({
  date: z.string(),
  title: z.string(),
  distance_km: z.number(),
  duration: z.string(),
  average_pace: z.string(),
  average_heart_rate: z.number(),
  elevation_gain_m: z.number(),
  mood: z.string(),
});

export type DailyRunShortProps = z.infer<typeof dailyRunShortSchema>;

// v0.9 template library. Each template below owns its own small, flat,
// publish-safe props contract. Field names again mirror aggregate metadata
// (weekly totals, race results, shoe usage) so the bundled sample JSON can be
// passed straight through with `--props`. No GPS, no raw clip filenames, and no
// location context ever cross this boundary (Decision 004).

// Weekly training recap: aggregate weekly totals plus a short summary line.
export const weeklyTrainingRecapSchema = z.object({
  week_of: z.string(),
  title: z.string(),
  total_distance_km: z.number(),
  total_duration: z.string(),
  runs: z.number(),
  total_elevation_gain_m: z.number(),
  best_pace: z.string(),
  summary: z.string(),
});

export type WeeklyTrainingRecapProps = z.infer<typeof weeklyTrainingRecapSchema>;

// Race day summary: a single race result with a one-line highlight.
export const raceDaySummarySchema = z.object({
  date: z.string(),
  race_name: z.string(),
  distance_km: z.number(),
  finish_time: z.string(),
  average_pace: z.string(),
  placement: z.string(),
  highlight: z.string(),
});

export type RaceDaySummaryProps = z.infer<typeof raceDaySummarySchema>;

// Data overlay clip: the small lower-third stats bar for compositing over
// footage. A deliberately minimal subset of the daily metrics.
export const dataOverlayClipSchema = z.object({
  date: z.string(),
  title: z.string(),
  distance_km: z.number(),
  average_pace: z.string(),
  average_heart_rate: z.number(),
});

export type DataOverlayClipProps = z.infer<typeof dataOverlayClipSchema>;

// Shoe review intro: shoe identity, usage, and a verdict. `rating` is a free
// string (for example "4.5 / 5") so the template stays presentation-only.
export const shoeReviewIntroSchema = z.object({
  shoe_name: z.string(),
  category: z.string(),
  total_distance_km: z.number(),
  rating: z.string(),
  verdict: z.string(),
});

export type ShoeReviewIntroProps = z.infer<typeof shoeReviewIntroSchema>;
