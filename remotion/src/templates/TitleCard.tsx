import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

// Shared title block: the run date (small, uppercase) above the working title.
// Designed to be reused by the v0.9 template library, so it takes only plain
// props and does its own entrance animation relative to a `delay` (in frames).
export const TitleCard: React.FC<{
  date: string;
  title: string;
  delay?: number;
}> = ({date, title, delay = 0}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const enter = spring({
    frame: frame - delay,
    fps,
    config: {damping: 200},
  });

  const translateY = interpolate(enter, [0, 1], [40, 0]);

  return (
    <div
      style={{
        opacity: enter,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <div
        style={{
          fontSize: 40,
          letterSpacing: 8,
          textTransform: 'uppercase',
          color: '#8bd3ff',
          fontWeight: 600,
          marginBottom: 24,
        }}
      >
        {date}
      </div>
      <div
        style={{
          fontSize: 84,
          lineHeight: 1.05,
          color: '#ffffff',
          fontWeight: 800,
        }}
      >
        {title}
      </div>
    </div>
  );
};
