# Antigravity Native Multi-Agent Dispatch Guide

In Google Antigravity 2.0, multi-agent orchestration is managed via native agent tools: `invoke_subagent`, `send_message`, and `manage_subagents`. This document establishes the operational patterns for running the creative writing agent staff.

---

## 1. Architectural Topology: Hub-and-Spoke

The system operates as a tiered hub-and-spoke hierarchy:
- **`muse`** sits at the center as the author-facing orchestrator (`model: inherit`, `mainAgent: true`, `subagent: false`).
- **Producer lanes** (`writer`, `outliner`, `brainstormer`, `style-creator`) generate material.
- **Reviewer lanes** (`critic`, `continuity-checker`, `reader-sim`, `cold-reader`) evaluate material objectively.
- **Sub-orchestrator** `kb-lead` manages knowledge capture lanes (`explorer`, `session-miner`, `kb-maintainer`).

---

## 2. Model Tier Allocation

Subagents are assigned model tiers based on cognitive demands, balancing creative depth with operational velocity:
- **Deep Creative & Critical Reasoning (`model: pro`)**:
  - `writer`: Rich narrative prose, voice maintenance, and nuanced line polishing.
  - `critic`: Rigorous adversarial diagnosis across structural pacing, character agency, and prose cadence.
  - `outliner`: Structural story architecture, thematic pacing, and chapter beat sheets.
  - `style-creator`: Linguistic voice analysis, stylistic rule extraction, and constraint design.
  - `kb-lead`: High-level taxonomy design, knowledge curation, and triage of durable canon.
- **High-Velocity Audit, Research & Simulation (`model: flash`)**:
  - `creative-researcher`: Rapid web research, historical context, and sensory detail gathering.
  - `continuity-checker`: Fact-checking and timeline verification against canon in `kb/`.
  - `reader-sim`: First-pass experiential reader reactions and emotional tracking.
  - `character-sim`: Fast, responsive in-character dialogue stress-testing.
  - `brainstormer`: Divergent narrative options and lateral brainstorming.
  - `explorer`, `session-miner`, `cold-reader`, `kb-maintainer`: Fast transcript parsing, reference searching, and markdown maintenance.
- **Primary Orchestrator (`muse`)**:
  - `model: inherit`: Inherits the author's primary conversation model in Antigravity Desktop or CLI.

---

## 3. Dispatching Subagents with `invoke_subagent`

### Native Call Schema
Antigravity's native `invoke_subagent` tool accepts an array of subagent specifications under `Subagents`, each specifying `TypeName`, `Role`, `Prompt`, and optional `Model` and `Workspace`:

### Parallel Review Lanes
When a draft is ready for review, `muse` spawns multiple review lanes concurrently in a single tool call:

```json
{
  "Subagents": [
    {
      "TypeName": "critic",
      "Role": "Adversarial Draft Critic",
      "Prompt": "Diagnose chapter 3 draft at work/drafts/ch03.md for emotional pacing and narrative tension. Return anchored findings.",
      "Model": "pro"
    },
    {
      "TypeName": "continuity-checker",
      "Role": "Canon Continuity Auditor",
      "Prompt": "Cross-reference chapter 3 draft at work/drafts/ch03.md against kb/timeline/timeline.md and kb/characters/alyssa.md. Flag any chronological or state contradictions.",
      "Model": "flash"
    },
    {
      "TypeName": "reader-sim",
      "Role": "Experiential Reader Reaction",
      "Prompt": "Perform an experiential cold read of work/drafts/ch03.md as a first-time fantasy reader. Record moment-by-moment emotional turns and confusions.",
      "Model": "flash"
    }
  ]
}
```

---

## 4. Multi-Turn Stateful Iteration vs. Fresh Cold Reads

### A. Stateful Producer Iteration (`writer`)
- The `writer` subagent maintains conversation history and context while idle.
- When `muse` receives feedback or revisions from the author, do NOT spawn a new `writer`.
- Instead, use `send_message` with the existing `writer` subagent conversation ID:
  ```json
  {
    "Recipient": "subagent-writer-id-12345",
    "Message": "The author accepted finding #2. Revise lines 45-60 to heighten Alyssa's hesitation before opening the vault. Keep the same prose rhythm."
  }
  ```
- This preserves stylistic momentum and prevents repetition.

### B. Fresh Cold Reads (`critic`, `reader-sim`)
- Reviewers must always provide an unvarnished, unbiased critique.
- If a draft is revised, spawn a **fresh** instance of `critic` or `reader-sim`. A reviewer that saw the earlier revision draft loses its clean naive reader perspective.

---

## 5. Nested Delegation (`kb-lead`)

`muse` does not need to micro-manage documentation refactoring. Instead:
1. `muse` invokes `kb-lead`:
   ```json
   {
     "Subagents": [
       {
         "TypeName": "kb-lead",
         "Role": "KB Lead: Chapter 3 Capture",
         "Prompt": "Update the knowledge base following completion of Chapter 3. Extract newly confirmed facts about the citadel into kb/world/locations.md.",
         "Model": "pro"
       }
     ]
   }
   ```
2. `kb-lead` in turn invokes `session-miner` to inspect conversation transcripts or `explorer` to check references, and delegates file updates to `kb-maintainer`.

---

## 6. Lifecycle Management with `manage_subagents`

Manage active background subagents when needed:
- **`list`**: Enumerate all active direct subagents with their conversation IDs and lifecycle state (`running`, `idle`, etc.).
- **`kill`**: Terminate specific subagents by conversation ID when a lane is cancelled or superseded.
- **`kill_all`**: Cleanly terminate all active subagent child processes.

Subagents report their results asynchronously back to the calling agent. Allow subagents to finish and synthesize the aggregated findings before presenting prioritized choices to the author.
