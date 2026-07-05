import React from 'react';
import {Background} from '../templates/Background';
import {MetricRow} from '../templates/MetricRow';
import {StatCallout} from '../templates/StatCallout';
import {TitleCard} from '../templates/TitleCard';
import {ACCENTS, GRADIENTS} from '../theme';
import type {WeeklyTrainingRecapProps} from '../types';

// Weekly training recap: leads with the week's total distance as the hero stat,
// then a stacked breakdown of the supporting weekly totals and a closing note.
// Built entirely from the shared template pieces, so it inherits the same look,
// animation, and privacy guarantees as the daily short.
export const WeeklyTrainingRecap: React.FC<WeeklyTrainingRecapProps> = ({
  week_of,
  title,
  total_distance_km,
  total_duration,
  runs,
  total_elevation_gain_m,
  best_pace,
  summary,
}) => {
  const metrics: {label: string; value: string}[] = [
    {label: 'Runs', value: `${runs}`},
    {label: 'Time', value: total_duration},
    {label: 'Elevation', value: `${total_elevation_gain_m} m`},
    {label: 'Best pace', value: best_pace},
  ];

  return (
    <Background gradient={GRADIENTS.weekly}>
      <TitleCard date={week_of} title={title} accent={ACCENTS.weekly} delay={0} />

      <StatCallout
        value={`${total_distance_km.toFixed(1)} km`}
        caption="Total this week"
        accent={ACCENTS.weekly}
        delay={10}
      />

      <div style={{display: 'flex', flexDirection: 'column', gap: 32}}>
        {metrics.map((metric, index) => (
          <MetricRow
            key={metric.label}
            label={metric.label}
            value={metric.value}
            delay={24 + index * 6}
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
        &ldquo;{summary}&rdquo;
      </div>
    </Background>
  );
};
