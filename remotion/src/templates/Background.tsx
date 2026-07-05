import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT_FAMILY} from '../theme';

// Shared vertical background used by every v0.9 template: a solid gradient (no
// bundled footage, so the public repo stays free of personal media), the shared
// font, consistent padding, and a gentle fade-out over the last half second so
// every clip ends cleanly. Given the same props the output is deterministic.
//
// Templates drop their own content in as children and lay it out; the wrapper
// only owns the look and the outro.
export const Background: React.FC<{
  gradient: string;
  children: React.ReactNode;
}> = ({gradient, children}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const outro = interpolate(
    frame,
    [durationInFrames - fps / 2, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill
      style={{
        background: gradient,
        fontFamily: FONT_FAMILY,
        opacity: outro,
      }}
    >
      <AbsoluteFill
        style={{
          padding: 120,
          justifyContent: 'space-between',
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
