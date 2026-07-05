import React from 'react';
import {Background} from '../templates/Background';
import {MetricRow} from '../templates/MetricRow';
import {StatCallout} from '../templates/StatCallout';
import {TitleCard} from '../templates/TitleCard';
import {ACCENTS, GRADIENTS} from '../theme';
import type {ShoeReviewIntroProps} from '../types';

// Shoe review intro: the opening card for a shoe review, leading with the shoe
// name and the distance logged on it as the hero stat, then category and rating,
// and a one-line verdict. Reuses the shared template pieces for a consistent
// look with the rest of the family.
export const ShoeReviewIntro: React.FC<ShoeReviewIntroProps> = ({
  shoe_name,
  category,
  total_distance_km,
  rating,
  verdict,
}) => {
  const metrics: {label: string; value: string}[] = [
    {label: 'Category', value: category},
    {label: 'Rating', value: rating},
  ];

  return (
    <Background gradient={GRADIENTS.shoe}>
      <TitleCard
        date="Shoe review"
        title={shoe_name}
        accent={ACCENTS.shoe}
        delay={0}
      />

      <StatCallout
        value={`${total_distance_km} km`}
        caption="Tested over"
        accent={ACCENTS.shoe}
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
        &ldquo;{verdict}&rdquo;
      </div>
    </Background>
  );
};
