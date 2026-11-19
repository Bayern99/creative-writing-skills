---
trigger: glob
globs: "kb/**/*.md, work/**/*.md"
---

# Knowledge Base & Work Notes Formatting Rules

When editing or creating knowledge base documents (`kb/**/*.md`) or work notes (`work/**/*.md`), follow these structural rules to ensure discoverability and link integrity:

## 1. Strict Relative Markdown Links
- Always use standard relative markdown links (e.g. `[Character Sheet](../characters/alyssa.md)` or `[Timeline](timeline.md)`).
- Never use machine-absolute paths (e.g. `/home/user/...`) or web URLs for local project files.
- Verify that every target file and header anchor exists before linking.
- When renaming or moving a knowledge base file, immediately update all incoming cross-references across `kb/` and `work/`.

## 2. Progressive Disclosure & Information Hierarchy
- Keep top-level files concise and skimmable. Provide summary tables, high-level overviews, and direct links to detailed deep-dives.
- Place granular details (full character histories, extensive magic system tables, chapter beat sheets) in dedicated subdocuments within topic folders.
- Avoid duplicate lore: cite the canonical document instead of copying large blocks of text between multiple files.

## 3. Metadata & Document Headers
- Maintain clear YAML frontmatter or standard markdown headers (`# Title`) on every page.
- Useful frontmatter fields:
  - `title`: Human-readable name of the topic, entity, or document.
  - `status`: Lifecycle state (e.g. `provisional`, `confirmed`, `deprecated`, `wip`).
  - `tags`: Relevant categories (e.g. `character`, `faction`, `location`, `outline`).
  - `last_updated`: Date of most recent revision.

## 4. Work Directory Discipline (`work/`)
- Treat files in `work/` as transient, active drafting spaces (e.g. `work/brainstorms/`, `work/outlines/`, `work/critiques/`).
- Once narrative decisions or lore elements settle in `work/`, distill the durable truths into canonical `kb/` documents and archive or clean up outdated scratch files.
