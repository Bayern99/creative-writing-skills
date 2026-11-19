---
name: atlas
description: Build a browsable map of a story's cast, factions, plot, or related worldbuilding using linked Mermaid pages and the bundled Atlas viewer.
---

# Atlas in Codex

Use the upstream Atlas method and its examples. Resolve its paths from the
installed plugin. [Atlas method](../../reference/skills/atlas/SKILL.md)

Copy the whole viewer template into the author's project when creating an
atlas, including its hidden context folder and example files. The installed
template accompanies the plugin; keep project-specific pages and config in
the writing workspace. For an existing atlas, use its current engine and
extend its pages unless the task also calls for an engine upgrade. [Viewer template and instructions](../../reference/skills/atlas/assets/atlas/README.md)

Check the linked pages with `node tools/atlas/check.mjs <config>`. Use the
bundled viewer for a local preview when the author wants to browse the map.
