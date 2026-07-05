import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

// Shared single-metric row: a label on the left, the value on the right.
// Reused for every run-data overlay and by the future v0.9 template library.
// Each row animates in relative to its own `delay` (in frames) so a list of
// rows can be staggered by the caller.
export const MetricRow: React.FC<{
  label: string;
  value: string;
  delay?: number;
}> = ({label, value, delay = 0}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const enter = spring({
    frame: frame - delay,
    fps,
    config: {damping: 200},
  });

  const translateX = interpolate(enter, [0, 1], [-60, 0]);

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        opacity: enter,
        transform: `translateX(${translateX}px)`,
        borderBottom: '2px solid rgba(255, 255, 255, 0.15)',
        paddingBottom: 20,
      }}
    >
      <span
        style={{
          fontSize: 38,
          letterSpacing: 4,
          textTransform: 'uppercase',
          color: 'rgba(255, 255, 255, 0.7)',
          fontWeight: 600,
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontSize: 58,
          color: '#ffffff',
          fontWeight: 800,
        }}
      >
        {value}
      </span>
    </div>
  );
};
