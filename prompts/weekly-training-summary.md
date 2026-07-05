---
id: weekly-training-summary
title: Weekly training summary
platforms: [youtube, instagram, facebook]
required_fields: [date]
description: Turn a representative run into a weekly training summary post.
---
You are helping a runner summarise a week of training around a representative
run. Keep the tone reflective and honest, and never invent stats that are not
provided. Where weekly totals are unknown, leave a clear placeholder for the
runner to fill in.

Representative run and context:
- Week ending: {{ date }}
- Activity: {{ activity_type }}
- Longest / key run distance: {{ metrics.distance_km }} km
- Average pace: {{ metrics.average_pace }}
- Training effect: {{ metrics.training_effect }}
- Mood across the week: {{ content_notes.mood }}
- Story angle: {{ content_notes.story_angle }}
- Lesson: {{ content_notes.lesson }}

Write the following, each clearly labelled:
1. A YouTube title and a bullet outline for a weekly recap video.
2. An Instagram caption reflecting on the week.
3. A Facebook post sharing the main takeaway.
4. Five relevant hashtags.
