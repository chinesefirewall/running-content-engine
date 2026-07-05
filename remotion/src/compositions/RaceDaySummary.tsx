import React from 'react';
import {Background} from '../templates/Background';
import {MetricRow} from '../templates/MetricRow';
import {StatCallout} from '../templates/StatCallout';
import {TitleCard} from '../templates/TitleCard';
import {ACCENTS, GRADIENTS} from '../theme';
import type {RaceDaySummaryProps} from '../types';

// Race day summary: the race name as the title, the finish time as the hero
// stat, then the supporting race metrics and a one-line highlight. Reuses the
// shared pieces so it matches the rest of the template family.
export const RaceDaySummary: React.FC<RaceDaySummaryProps> = ({
  date,
  race_name,
  distance_km,
  finish_time,
  average_pace,
  placement,
  highlight,
}) => {
  const metrics: {label: string; value: string}[] = [
    {label: 'Distance', value: `${distance_km.toFixed(1)} km`},
    {label: 'Avg pace', value: average_pace},
    {label: 'Placement', value: placement},
  ];

  return (
    <Background gradient={GRADIENTS.race}>
      <TitleCard date={date} title={race_name} accent={ACCENTS.race} delay={0} />

      <StatCallout
        value={finish_time}
        caption="Finish time"
        accent={ACCENTS.race}
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
        &ldquo;{highlight}&rdquo;
      </div>
    </Background>
  );
};
