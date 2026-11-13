---
name: writing-staffing
description: |
  Load before you hand story work to another agent: which agent takes which lane, which skills to tell it to load, which files to pass, how many lanes to run, and which model to run them on.
metadata:
  type: reference
---

# Writing Staffing

Each agent loads its core skills itself. Your brief adds the rest: the lane,
the extra skills to tell it to load ("load `/character-sim`"), the files to
pass, the reader effect to create, and what to leave ambiguous or unresolved.
The files each kind of work needs are in `/story-memory`
`resources/story-context.md` § What Each Agent Needs.

## Model Selection & Multi-Agent Dispatch

In Antigravity, invoke agents via `invoke_subagent`. See `resources/antigravity-dispatch.md` for full dispatch patterns.

The author selects the primary session model in the App/CLI. `muse` and the five specialists `writer`, `critic`, `outliner`, `style-creator`, and `kb-lead` use `model: inherit`; the other nine specialists use `model: flash`. Select standalone Gemini 4 Hydrogen for a Hydrogen + Flash workflow. If the author selects a different main model, the inherited specialists follow that model. The `flash` tier is resolved by Antigravity; check the actual child model in the running session.

**Parallel lanes**: In `invoke_subagent`, you can pass multiple subagent definitions in a single call (e.g. structure, voice, and character critics) to run concurrently.

**Multi-turn conversations**: `writer` retains context while idle. Use `send_message` to send round-2 revision feedback to the same `writer` instance to keep voice consistent. For reviewers (`critic`, `reader-sim`), open fresh instances each round for a clean cold-read perspective.

## Agent Catalogs

- `resources/producers.md`: `@writer`, `@brainstormer`, `@outliner`,
  `@style-creator`, `@character-sim`, `@creative-researcher`, and `@kb-lead`. Open
  it before you spawn an agent that writes or gathers.
- `resources/reviewers.md`: `@critic` lanes (a focus area or an edit level),
  `@continuity-checker`, `@reader-sim`, and how many lanes a chapter needs.
  Open it before staffing any critique.
