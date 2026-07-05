// Shared brand kit for the v0.9 template library.
//
// Keeping the font, gradients, and accent colours in one place is what lets the
// daily short, weekly recap, race-day summary, data-overlay clip, and
// shoe-review intro share a consistent look while each still has its own accent.
// Every template pulls from here so a future re-brand is a single-file change.
export const FONT_FAMILY =
  'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

// One gradient per content type. Same shape, different hue, so the set feels
// like a family without every video looking identical.
export const GRADIENTS = {
  daily: 'linear-gradient(160deg, #0b1f33 0%, #123a5c 60%, #0b1f33 100%)',
  weekly: 'linear-gradient(160deg, #10231a 0%, #1b5138 60%, #10231a 100%)',
  race: 'linear-gradient(160deg, #2a1533 0%, #5c1240 60%, #2a1533 100%)',
  overlay: 'linear-gradient(160deg, #14161c 0%, #22252e 60%, #14161c 100%)',
  shoe: 'linear-gradient(160deg, #33240b 0%, #5c3f12 60%, #33240b 100%)',
} as const;

// The accent colour used for dates, labels, and hero numbers per content type.
export const ACCENTS = {
  daily: '#8bd3ff',
  weekly: '#7ff0b0',
  race: '#ff8bd0',
  overlay: '#c7d2ff',
  shoe: '#ffcf8b',
} as const;
