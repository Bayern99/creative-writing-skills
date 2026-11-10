# Creative Writing Plugin for Google Antigravity 2.0

[![Antigravity 2.0](https://img.shields.io/badge/Antigravity-2.0-blue.svg)](https://antigravity.google)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A composable, native multi-agent system and craft skill library for creative writing projects in Google Antigravity 2.0.

---

## Overview

The `creative-writing-skills` plugin turns Google Antigravity into a dedicated creative writing studio. At its center is **Muse**, your creative partner that talks through story ideas, outlines narrative arcs, collaborates on prose, and orchestrates specialized subagent lanes for critique, continuity checking, reader simulation, and knowledge capture.

### Key Architectural Highlights
- **Native Antigravity Multi-Agent Architecture**: Built specifically for Antigravity's `invoke_subagent` and `send_message` capabilities.
- **Optimized Model Strategy**:
  - **Muse (`model: inherit`)**: Operates on the model you select in Antigravity Desktop or CLI.
  - **14 Specialized Subagents (`model: flash`)**: Fast, high-throughput execution on Gemini 3.8 Flash, with role specialization driven by focused system instructions and tailored skill bundles.
- **Safety First**: Integrated `PreToolUse` git guard hook preventing accidental destructive git actions (`git reset --hard`, `git clean`, etc.).
- **Complete Creative Lifecycle**: From initial worldbuilding interview (`/project-setup`) to accepted manuscript pages and synchronized knowledge bases.

---

## Agent Roster (15 Agents)

### Main Agents (Available in Antigravity Agent Selector)
1. **`muse`** (Orchestrator, `model: inherit`): Primary creative partner. Leads story discussions, maintains the project vision, dispatches subagents, and owns the verdict on drafts.
2. **`writer`** (Producer, `model: flash`): Produces production prose (fresh drafts, revisions, bridges, alternate takes, or line polishes).
3. **`character-sim`** (Simulator, `model: flash`): In-character conversational partner for voice discovery and dialogue stress-testing.
4. **`outliner`** (Planner, `model: flash`): Turns story directions into structured saga, arc, chapter, and scene beat outlines.

### Specialized Subagents (Spawned on Demand by Muse or KB Lead)
5. **`critic`** (Reviewer): Deep diagnostic review across structure, pacing, voice, prose, and dialogue.
6. **`continuity-checker`** (Reviewer): Cross-references drafts against project canon, character state, and timeline in `kb/`.
7. **`reader-sim`** (Reviewer/Simulator): Experiential, moment-by-moment naive reader feedback.
8. **`brainstormer`** (Producer): Generates divergent narrative options with explicit tradeoffs.
9. **`style-creator`** (Producer/Analyst): Analyzes prose samples to establish style guides and voice rules.
10. **`creative-researcher`** (Researcher): Fact and lore grounding for historical, cultural, or domain accuracy.
11. **`kb-lead`** (Sub-orchestrator): Coordinates knowledge extraction and durable documentation updates.
12. **`explorer`** (Reviewer/Explorer): Deep cross-file analysis and repository search without editing files.
13. **`session-miner`** (Reviewer): Extracts decisions, rejected alternatives, and intent from session transcripts.
14. **`cold-reader`** (Reviewer): Audits project documentation for clarity to an outside reader.
15. **`kb-maintainer`** (Maintainer): Structural refactoring, link maintenance, and tidying of the `kb/` tree.

---

## 28 Bundled Craft Skills

The plugin packages 28 modular skills covering every aspect of writing craft:
- **Writing Craft & Style**: `creative-writing-craft`, `writing-principles`, `llm-writing`, `writing-staffing`, `creative-writing-muse`.
- **Planning & Architecture**: `story-planning`, `story-workflow`, `intent-modeling`, `grill`, `grill-with-docs`.
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
agy plugin install https://github.com/haowjy/creative-writing-skills/tree/main/plugin/antigravity
```

### Antigravity Desktop App
1. Navigate to **Settings** -> **Plugins**.
2. Click **Install Plugin** and select the `plugin/antigravity` folder or paste the GitHub URL.
3. Confirm that `creative-writing-skills` is active.

---

## Getting Started

### 1. Initialize a Story Project
In your project directory, run:
```text
/project-setup
```
Answer the setup interview questions. The skill will scaffold your `AGENTS.md` and initial `kb/` directory hierarchy (`characters/`, `world/`, `timeline/`, `styles/`).

### 2. Launch Muse
In Antigravity Desktop App, select **`muse`** from the Agent dropdown. In CLI:
```bash
agy --agent muse
```

### 3. Plan, Draft, and Review
- **Brainstorm & Outline**: *"Muse, let's explore possibilities for the climax of Act 1."* Muse will engage with you, record decisions, and dispatch `outliner`.
- **Drafting**: *"Let's draft Scene 1 from the outline."* Muse coordinates with `writer` using the voice defined in `kb/styles/`.
- **Multi-Lane Review**: When a scene is ready, Muse invokes `critic`, `continuity-checker`, and `reader-sim` concurrently for actionable feedback.
- **Knowledge Capture**: When the scene is approved, Muse dispatches `kb-lead` to keep character sheets and timelines current.

---

## Destructive Git Guard

The plugin includes an active `PreToolUse` hook (`scripts/git_guard.py`) that monitors terminal commands executed by agents. If an agent attempts a destructive git operation (such as `git reset --hard`, `git clean`, `git restore`, `git checkout --`, or `git revert`), the hook prompts you for confirmation (`decision: ask`) before executing, safeguarding your story manuscript.

---

## License

Distributed under the Apache 2.0 License. See [LICENSE](LICENSE) for details.
