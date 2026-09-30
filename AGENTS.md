# HogMorphStudio project skills

## grill-me

- Project-local entry point: `.agents/skills/grill-me/SKILL.md`.
- Dependency: `.agents/skills/grilling/SKILL.md`.
- When the user explicitly invokes `$grill-me`, `/grill-me`, or asks to use grill-me, read the entry point and its dependency before starting the session.
- Installation/configuration requests do not invoke a grilling session.
- Discuss the project in Chinese unless the user requests another language. Follow the upstream design-tree rounds: offer recommendations, investigate repository facts yourself, and wait for answers to user decisions.
- The skill's discussion scope does not authorize new external messages, destructive actions, or production changes.

Upstream source, pinned revision, and MIT license are included in each installed skill directory.
