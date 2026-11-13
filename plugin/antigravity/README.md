# Creative Writing Plugin for Google Antigravity 2.0

[![Antigravity 2.0](https://img.shields.io/badge/Antigravity-2.0-blue.svg)](https://antigravity.google)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A native Antigravity plugin with 15 agents and 27 skills for writing fiction.

---

## Overview

**Muse** talks through story ideas, plans and drafts with you, and delegates critique, continuity checks, reader simulation, research, and knowledge capture to specialist agents.

Agents use Antigravity's native `invoke_subagent` and `send_message` tools, with dedicated prompts, tool permissions, and skill bundles. `/project-setup` establishes the story project; `/story-workflow` guides work through planning, drafting, review, and knowledge capture.

## Model Selection: Inherited Specialists + Flash

Choose any available model for **Muse** in the main conversation's model picker. The five creative specialists inherit that choice:

| Agents | Configuration | Purpose |
| --- | --- | --- |
| `muse` | Main conversation selection | Creative direction, drafting, delegation, final judgment |
| `writer`, `critic`, `outliner`, `style-creator`, `kb-lead` | `model: inherit` | Prose, editorial judgment, structure, voice, and knowledge decisions |
| The other 9 specialists | `model: flash` | Focused research, simulation, retrieval, checks, and structural maintenance |

`inherit` follows the calling agent's model. With Hydrogen selected, those five specialists use Hydrogen; changing the parent model changes their inherited model too. This configuration does not pin Hydrogen independently of the parent. The Flash tier targets Gemini 3.8 Flash in the current service; inspect the resolved model in a subagent's details when checking routing.

The [plugin schema](https://antigravity.google/docs/build-plugins) accepts model tiers (`inherit`, `flash_lite`, `flash`, `pro`), while the [model picker](https://antigravity.google/docs/models) selects the primary model. Orchestrator has its own planning/execution routing. Choosing standalone Hydrogen is one option for the main session.

---

## Agent Roster (15 Agents)

Muse is the main creative partner; it can delegate to 14 specialists. Writer, character-sim, and outliner are also available as primary agents. When you select one directly, choose its session model in the app; the tier column below applies to delegated work.

| Agent | Delegated tier | Responsibility |
| --- | --- | --- |
| `muse` | Main agent only | Discussion, plans, drafts, and final verdicts |
| `writer` | `inherit` | Drafts, revisions, bridges, alternate takes, and line polish |
| `outliner` | `inherit` | Narrative arcs, chapter beats, and scene structures |
| `critic` | `inherit` | Editorial diagnosis with findings anchored to the draft |
| `style-creator` | `inherit` | Concrete voice and style guidance from prose samples |
| `kb-lead` | `inherit` | Writes settled knowledge, deletes stale content, and reorganizes affected pages |
| `character-sim` | `flash` | Character voice, motivation, and dialogue simulation |
| `continuity-checker` | `flash` | Canon, character-state, and timeline checks |
| `reader-sim` | `flash` | First-read reactions, clarity, suspense, and payoff |
| `brainstormer` | `flash` | Distinct narrative options and their tradeoffs |
| `creative-researcher` | `flash` | Historical, cultural, and domain research |
| `explorer` | `flash` | Scoped evidence retrieval with paths, lines, and snippets |
| `session-miner` | `flash` | Finds transcript passages; the caller judges what they settled |
| `cold-reader` | `flash` | Documentation clarity for an outside reader |
| `kb-maintainer` | `flash` | Whole-tree structural changes and link repair |

---

## 27 Bundled Craft Skills

The plugin packages these skills:

- **Writing Craft & Style**: `creative-writing-craft`, `writing-principles`, `llm-writing`, `writing-staffing`, `creative-writing-muse`.
- **Planning & Architecture**: `story-planning`, `story-workflow`, `intent-modeling`, `grill`.
- **Review & Continuity**: `story-review`, `reader-sim`, `character-sim`, `md-validation`, `shared-dao`.
- **Knowledge Governance**: `story-memory`, `knowledge-layers`, `qi-layer`, `qi-maintenance`, `information-hierarchy`, `correct`, `reflect`, `zoom-out`, `shared-workspace`.
- **Research & Setup**: `project-setup`, `creative-research`, `structured-artifact`, `writing-sync`.

---

## Installation

### Antigravity CLI
Install from your local repository:
```bash
agy plugin install ./plugin/antigravity
```
Or directly from GitHub:
```bash
agy plugin install https://github.com/Bayern99/creative-writing-skills/tree/antigravity-plugin/plugin/antigravity
```

### Antigravity Desktop App

For a manual App installation, place the complete `plugin/antigravity/` directory at `~/.gemini/config/plugins/creative-writing-skills/`, or at `.agents/plugins/creative-writing-skills/` inside one project. When updating a manual installation, replace the installed plugin directory as a whole so removed skills do not remain. Open **Customizations** in the left sidebar, select **Installed**, and inspect the enabled plugin's agents and skills. These are the [documented App installation locations](https://antigravity.google/docs/plugins).

---

## Getting Started

### 1. Initialize a Story Project
In your project directory, run:
```text
/project-setup
```
Answer the setup interview questions. The skill will scaffold your `AGENTS.md` and initial `kb/` directory hierarchy (`characters/`, `world/`, `timeline/`, `styles/`).

### 2. Launch Muse
In Antigravity Desktop App, select **`muse`** from the Agent dropdown and choose your preferred model in the model picker. In CLI:
```bash
agy --agent muse
```

### 3. Plan, Draft, and Review

- **Brainstorm & Outline**: *"Muse, let's explore possibilities for the climax of Act 1."* Muse discusses directions with you and can delegate a separate structural pass to `outliner`.
- **Drafting**: *"Let's draft Scene 1 from the outline."* Muse drafts with you using the voice in `kb/styles/`, or delegates a fresh draft, revision, alternate take, polish pass, or long draft to `writer`.
- **Multi-Lane Review**: When a scene is ready, Muse invokes `critic`, `continuity-checker`, and `reader-sim` concurrently for actionable feedback.
- **Knowledge Capture**: When the scene is approved, Muse dispatches `kb-lead` to keep character sheets and timelines current.

---

## Seeing What Subagents Are Doing

Antigravity App v2.30.0 introduced **Knowledge Work** layout. It replaces subagent cards and expandable tool groups with a live progress line; agents still execute and return their results. The **Software Engineering** layout exposes those controls. See [Interface Layout](https://antigravity.google/docs/settings) and the [App changelog](https://antigravity.google/docs/changelog).

1. Open **Settings > General > Interface Layout** and select **Software Engineering**. The change applies immediately. Business and enterprise accounts already use this layout.
2. Open the conversation's **Overview** panel at the top right, then **Subagents** and select the agent to read its conversation in the side panel. If the section is hidden, enable **Customize Sections > Subagents**. Use **See all** for completed agents. See [Side panel and Overview](https://antigravity.google/docs/side-panel/).
3. If the expected agent is absent, expand the dispatch tool call and check that it used native `invoke_subagent` with the intended `TypeName`. A separate terminal/SDK process has a different session and will not supply that native subagent card.

In the CLI, open `/agents` and select the child to inspect its conversation and resolved model. Preserve the child conversation ID when reporting a visibility or routing issue. A final walkthrough is an output artifact; the running conversation is opened through the Subagents section.

---

## Destructive Git Guard

The plugin includes an active `PreToolUse` hook (`scripts/git_guard.py`) that monitors terminal commands executed by agents. If an agent attempts a destructive git operation (such as `git reset --hard`, `git clean`, `git restore`, `git checkout --`, or `git revert`), the hook prompts you for confirmation (`decision: ask`) before executing, safeguarding your story manuscript.

---

## License

Distributed under the Apache 2.0 License. See [LICENSE](LICENSE) for details.
