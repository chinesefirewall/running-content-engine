---
id: shoe-review
title: Shoe review
platforms: [youtube, instagram, tiktok, facebook, shorts]
required_fields: [date, gear.shoes]
description: Turn a run into an honest review of the shoes used.
---
You are helping a runner write an honest, useful review of a running shoe based
on a real run. Do not exaggerate; only use the data provided and clearly note
where more testing is needed.

Shoe and run data:
- Date: {{ date }}
- Shoes: {{ gear.shoes }}
- Activity: {{ activity_type }}
- Distance: {{ metrics.distance_km }} km
- Average pace: {{ metrics.average_pace }}
- Surface: {{ conditions.surface }}
- Conditions: {{ conditions.weather }}, {{ conditions.temperature_c }} C
- How they felt (mood / notes): {{ content_notes.mood }}
- Key moment: {{ content_notes.key_moment }}
- Lesson / takeaway: {{ content_notes.lesson }}

Write the following, each clearly labelled:
1. A YouTube title and a short review outline (fit, cushioning, ride, value).
2. An Instagram caption summarising the verdict in one line plus detail.
3. A TikTok / Shorts hook (one honest opinion).
4. A Facebook post inviting questions.
5. Five relevant hashtags.
