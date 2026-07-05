import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../templates/Background';
import {ACCENTS, GRADIENTS} from '../theme';
import type {DataOverlayClipProps} from '../types';

// Data overlay clip: a lower-third stats bar designed to sit over running
// footage. In the public repo it renders over the shared placeholder gradient
// (no personal media); locally it can be rendered with an alpha channel (e.g.
// a ProRes/WebM codec with a transparent background) and composited over real
// `raw/` footage. Only aggregate, publish-safe metrics are shown.
export const DataOverlayClip: React.FC<DataOverlayClipProps> = ({
  date,
  title,
  distance_km,
  average_pace,
  average_heart_rate,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const enter = spring({frame, fps, config: {damping: 200}});
  const translateY = interpolate(enter, [0, 1], [80, 0]);

  const stats: {label: string; value: string}[] = [
    {label: 'Distance', value: `${distance_km.toFixed(1)} km`},
    {label: 'Pace', value: average_pace},
    {label: 'HR', value: `${average_heart_rate} bpm`},
  ];

  return (
    <Background gradient={GRADIENTS.overlay}>
      {/* Spacer so the panel is pushed to the bottom (lower third). */}
      <div />

      <div
        style={{
          opacity: enter,
          transform: `translateY(${translateY}px)`,
          background: 'rgba(10, 12, 18, 0.72)',
          borderRadius: 32,
          border: '2px solid rgba(255, 255, 255, 0.12)',
          padding: 56,
        }}
      >
        <div
          style={{
            fontSize: 32,
            letterSpacing: 6,
            textTransform: 'uppercase',
            color: ACCENTS.overlay,
            fontWeight: 600,
            marginBottom: 12,
          }}
        >
          {date}
        </div>
        <div
          style={{
            fontSize: 56,
            color: '#ffffff',
            fontWeight: 800,
            marginBottom: 40,
            lineHeight: 1.05,
          }}
        >
          {title}
        </div>

        <div style={{display: 'flex', justifyContent: 'space-between', gap: 32}}>
          {stats.map((stat) => (
            <div key={stat.label} style={{textAlign: 'center', flex: 1}}>
              <div style={{fontSize: 64, color: '#ffffff', fontWeight: 800}}>
                {stat.value}
              </div>
              <div
                style={{
                  fontSize: 30,
                  letterSpacing: 4,
                  textTransform: 'uppercase',
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontWeight: 600,
                  marginTop: 8,
                }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Background>
  );
};
