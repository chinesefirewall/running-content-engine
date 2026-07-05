import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

// Shared hero-stat block: one large number with a small caption underneath.
// Used by templates that lead with a single headline figure (weekly total
// distance, race finish time, distance on a pair of shoes). Like the other
// shared pieces it takes plain props and animates in relative to a `delay`.
export const StatCallout: React.FC<{
  value: string;
  caption: string;
  accent?: string;
  delay?: number;
}> = ({value, caption, accent = '#ffffff', delay = 0}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const enter = spring({
    frame: frame - delay,
    fps,
    config: {damping: 200},
  });

  const scale = interpolate(enter, [0, 1], [0.8, 1]);

  return (
    <div
      style={{
        opacity: enter,
        transform: `scale(${scale})`,
        textAlign: 'center',
      }}
    >
      <div
        style={{
          fontSize: 160,
          lineHeight: 1,
          color: accent,
          fontWeight: 800,
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: 40,
          letterSpacing: 6,
          textTransform: 'uppercase',
          color: 'rgba(255, 255, 255, 0.7)',
          fontWeight: 600,
          marginTop: 20,
        }}
      >
        {caption}
      </div>
    </div>
  );
};
