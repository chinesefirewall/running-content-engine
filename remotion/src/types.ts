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
