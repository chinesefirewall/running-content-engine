---
id: race-day-recap
title: Race day recap
platforms: [youtube, instagram, tiktok, facebook, shorts]
required_fields: [date, activity_type, metrics.distance_km]
description: Turn a race performance into an emotional, multi-platform recap.
---
You are helping a runner tell the story of a race day. Focus on the emotional
arc (before, during, after), keep the voice honest, and never invent stats
that are not provided.

Race data:
- Date: {{ date }}
- Activity: {{ activity_type }}
- Recording type: {{ recording_type }}
- Distance: {{ metrics.distance_km }} km
- Finish time / duration: {{ metrics.duration }}
- Average pace: {{ metrics.average_pace }}
- Average heart rate: {{ metrics.average_heart_rate }} bpm
- Max heart rate: {{ metrics.max_heart_rate }} bpm
- Elevation gain: {{ metrics.elevation_gain_m }} m
- Conditions: {{ conditions.weather }}, {{ conditions.temperature_c }} C
- Working title: {{ title_working }}
- Story angle: {{ content_notes.story_angle }}
- Hook idea: {{ content_notes.hook }}
- Key moment: {{ content_notes.key_moment }}
- Lesson: {{ content_notes.lesson }}

Write the following, each clearly labelled:
1. A YouTube title and a one-paragraph description.
2. An Instagram caption that captures the emotion of the race.
3. A TikTok / Shorts hook built around the key moment.
4. A Facebook post thanking supporters.
5. Five relevant hashtags.
