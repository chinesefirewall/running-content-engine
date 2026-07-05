import React from 'react';
import {Composition} from 'remotion';
import {DailyRunShort} from './compositions/DailyRunShort';
import {DataOverlayClip} from './compositions/DataOverlayClip';
import {RaceDaySummary} from './compositions/RaceDaySummary';
import {ShoeReviewIntro} from './compositions/ShoeReviewIntro';
import {WeeklyTrainingRecap} from './compositions/WeeklyTrainingRecap';
import sampleOverlay from './data/sample-overlay.json';
import sampleRace from './data/sample-race.json';
import sampleRun from './data/sample-run.json';
import sampleShoe from './data/sample-shoe.json';
import sampleWeek from './data/sample-week.json';
import {
  dailyRunShortSchema,
  dataOverlayClipSchema,
  raceDaySummarySchema,
  shoeReviewIntroSchema,
  weeklyTrainingRecapSchema,
} from './types';

// Registers every composition in the v0.9 template library. All share the same
// vertical 1080x1920 / 30fps format; only the duration and props differ.
const FPS = 30;
const WIDTH = 1080;
const HEIGHT = 1920;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DailyRunShort"
        component={DailyRunShort}
        durationInFrames={FPS * 13}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        schema={dailyRunShortSchema}
        defaultProps={sampleRun}
      />
      <Composition
        id="WeeklyTrainingRecap"
        component={WeeklyTrainingRecap}
        durationInFrames={FPS * 14}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        schema={weeklyTrainingRecapSchema}
        defaultProps={sampleWeek}
      />
      <Composition
        id="RaceDaySummary"
        component={RaceDaySummary}
        durationInFrames={FPS * 13}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        schema={raceDaySummarySchema}
        defaultProps={sampleRace}
      />
      <Composition
        id="DataOverlayClip"
        component={DataOverlayClip}
        durationInFrames={FPS * 8}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        schema={dataOverlayClipSchema}
        defaultProps={sampleOverlay}
      />
      <Composition
        id="ShoeReviewIntro"
        component={ShoeReviewIntro}
        durationInFrames={FPS * 12}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        schema={shoeReviewIntroSchema}
        defaultProps={sampleShoe}
      />
    </>
  );
};
