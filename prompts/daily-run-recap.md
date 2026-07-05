---
id: daily-run-recap
title: Daily run recap
platforms: [youtube, instagram, tiktok, facebook, shorts]
required_fields: [date, activity_type, metrics.distance_km]
description: Turn a single day's run into multi-platform recap content.
---
You are helping a runner document their training authentically. Keep their
honest voice, avoid clickbait, and never invent stats that are not provided.

Run data:
- Date: {{ date }}
- Activity: {{ activity_type }}
- Distance: {{ metrics.distance_km }} km
- Duration: {{ metrics.duration }}
- Average pace: {{ metrics.average_pace }}
- Average heart rate: {{ metrics.average_heart_rate }} bpm
- Conditions: {{ conditions.weather }}, {{ conditions.temperature_c }} C
- Mood: {{ content_notes.mood }}
- Story angle: {{ content_notes.story_angle }}
- Hook idea: {{ content_notes.hook }}
- Lesson: {{ content_notes.lesson }}
- Key moment: {{ content_notes.key_moment }}

Write the following, each clearly labelled:
1. A YouTube title (no clickbait).
2. An Instagram caption with a strong first line.
3. A TikTok / Shorts hook (one or two lines).
4. A short Facebook post.
5. Five relevant hashtags.
