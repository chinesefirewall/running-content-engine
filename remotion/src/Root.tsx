import React from 'react';
import {Composition} from 'remotion';
import {DailyRunShort} from './compositions/DailyRunShort';
import sampleRun from './data/sample-run.json';
import {dailyRunShortSchema} from './types';

// Registers every composition available to the Studio and the render CLI.
// For the v0.8 prototype there is exactly one: a vertical daily run short.
const FPS = 30;
const DURATION_SECONDS = 13;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="DailyRunShort"
      component={DailyRunShort}
      durationInFrames={FPS * DURATION_SECONDS}
      fps={FPS}
      width={1080}
      height={1920}
      schema={dailyRunShortSchema}
      defaultProps={sampleRun}
    />
  );
};
