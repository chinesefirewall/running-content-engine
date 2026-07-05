import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {MetricRow} from '../templates/MetricRow';
import {TitleCard} from '../templates/TitleCard';
import type {DailyRunShortProps} from '../types';

// The one prototype composition (v0.8).
//
// It renders a vertical daily run short from the publish-safe props contract.
// The background is a solid gradient (no bundled footage) so the public repo
// stays free of personal media; real `raw/` footage can be wired in locally
// later. Given the same props, the output is deterministic.
export const DailyRunShort: React.FC<DailyRunShortProps> = ({
  date,
  title,
  distance_km,
  duration,
  average_pace,
  average_heart_rate,
  elevation_gain_m,
  mood,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  // Gentle fade-out over the last half second so the clip ends cleanly.
  const outro = interpolate(
    frame,
    [durationInFrames - fps / 2, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  const metrics: {label: string; value: string}[] = [
    {label: 'Distance', value: `${distance_km.toFixed(1)} km`},
    {label: 'Duration', value: duration},
    {label: 'Avg pace', value: average_pace},
    {label: 'Avg HR', value: `${average_heart_rate} bpm`},
    {label: 'Elevation', value: `${elevation_gain_m} m`},
  ];

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(160deg, #0b1f33 0%, #123a5c 60%, #0b1f33 100%)',
        fontFamily:
          'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        padding: 96,
        opacity: outro,
      }}
    >
      <AbsoluteFill
        style={{
          padding: 96,
          justifyContent: 'space-between',
        }}
      >
        <TitleCard date={date} title={title} delay={0} />

        <div style={{display: 'flex', flexDirection: 'column', gap: 32}}>
          {metrics.map((metric, index) => (
            <MetricRow
              key={metric.label}
              label={metric.label}
              value={metric.value}
              delay={12 + index * 6}
            />
          ))}
        </div>

        <div
          style={{
            fontSize: 44,
            fontStyle: 'italic',
            color: 'rgba(255, 255, 255, 0.85)',
            lineHeight: 1.3,
          }}
        >
          &ldquo;{mood}&rdquo;
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
