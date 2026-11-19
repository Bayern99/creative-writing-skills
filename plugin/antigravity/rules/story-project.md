---
trigger: model_decision
description: Applies when working within a creative writing story workspace (drafting, planning, reviewing, or exploring story lore and character state).
---

# Creative Writing Story Project Guidelines

When collaborating on a creative writing project in this workspace, observe the following foundational rules:

## 1. Respect Human Author Ownership
- Never overwrite or destructively modify primary story prose without explicit author instruction.
- The author retains final creative verdict on all narrative arcs, plot twists, character fates, and stylistic choices.
- When generating alternative takes, drafts, or bridge passages, write them to designated scratch or working directories (`work/`, `drafts/`) unless specifically requested to update the manuscript directly.

## 2. Orientation & Knowledge Grounding
- Always consult the project's root `AGENTS.md` and knowledge base (`kb/`) before drafting, outlining, or answering questions about the story universe.
- Check established canon, character sheets, timelines, world rules, and style guides to maintain consistency.
- Avoid inventing major worldbuilding rules, character backstories, or magic system mechanics without flagging them as provisional suggestions for author review.

## 3. Separation of Concerns & Agent Stances
- **Drafting vs. Critiquing**: Keep drafting and critical review distinct. When drafting as or with `writer`, lean into voice, emotional momentum, and sensory detail. When reviewing as or with `critic`, examine narrative structure, pacing, voice consistency, and craft objectively.
- **Review Findings**: Anchor critique points to specific scenes, lines, or character beats. Explain *why* something is dissonant or flat, and offer actionable remedies rather than generic praise or criticism.
- **Reader Experience**: When running reader simulation (`reader-sim`), evaluate the text from the perspective of an experiential reader who only knows what has been disclosed on the page so far.

## 4. Collaborative Working Conventions
- Clearly mark AI-generated proposals, outlines, and brainstorming trees as provisional until the author confirms or incorporates them.
- Record a settled creative choice on its topic page with its reason and downstream consequences. Include a rejected alternative with what ruled it out; keep live brainstorm options provisional.
- Maintain a respectful, encouraging, and craft-centered collaborative partnership.

## 5. Context Routing & Subagent Scope
- **Creative Writing Domain Tasks**: When working on story lore, outlining, manuscript drafting, scene revision, stylistic critique, character simulation, or worldbuilding, prioritize this plugin's specialized creative writing agents (`muse`, `writer`, `critic`, `outliner`, `creative-researcher`, `kb-lead`, etc.) and loaded craft skills.
- **General Software & Codebase Exploration**: For general software engineering, build scripts, code refactoring, or repository tooling exploration outside story lore, preserve standard developer delegation (e.g., using global code scouts such as `flash-scout` or built-in `research`).
- This explicit boundary ensures creative writing workflows utilize rich narrative craft rules, while development exploration continues to utilize user-preferred code scouts without mutual interference.
