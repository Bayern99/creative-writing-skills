# Antigravity Native Multi-Agent Dispatch Guide

In Google Antigravity 2.0, multi-agent orchestration is managed via native agent tools: `invoke_subagent`, `send_message`, and `manage_subagents`. This document establishes the operational patterns for running the creative writing agent staff.

---

## 1. Architectural Topology: Hub-and-Spoke

The system operates as a tiered hub-and-spoke hierarchy:
- **`muse`** sits at the center as the author-facing orchestrator (`model: inherit`, `mainAgent: true`, `subagent: false`). Muse owns creative direction, subagent orchestration, synthesis, and final quality verdicts.
- **Producer lanes** (`writer`, `outliner`, `brainstormer`, `style-creator`) generate material.
- **Reviewer lanes** (`critic`, `continuity-checker`, `reader-sim`, `cold-reader`) evaluate material objectively.
- **Research & Simulation lanes** (`creative-researcher`, `character-sim`) provide factual grounding and interactive dialogue testing.
- **Sub-orchestrator** `kb-lead` manages knowledge capture lanes (`explorer`, `session-miner`, `cold-reader`, `kb-maintainer`).

---

## 2. Model Tier Allocation

- **`muse` (`model: inherit`)**: Inherits the author's chosen session model in Antigravity Desktop or CLI, owning creative direction, orchestration, result integration, and final quality judgment.
- **All 14 Subagents (`model: flash`)**: Configured uniformly to `model: flash` (Gemini 3.8 Flash) for fast, high-throughput parallel execution across all specialist lanes (`writer`, `critic`, `outliner`, `style-creator`, `kb-lead`, `creative-researcher`, `continuity-checker`, `reader-sim`, `character-sim`, `brainstormer`, `explorer`, `session-miner`, `cold-reader`, and `kb-maintainer`).
- **Role Differentiation**: Specialist independence comes from dedicated system prompts, explicit least-privilege `tools` allowlists, and targeted craft skill bundles.

---

## 3. Dispatching Subagents with `invoke_subagent`

### Native Call Schema
Per the official Antigravity Hooks and Subagents documentation, `invoke_subagent` accepts a `Subagents` array where each entry defines `TypeName`, `Role`, `Prompt`, and optional `Workspace` (`inherit`, `branch`, or `share`).
*(Note: Each subagent's model tier is governed by its frontmatter `model: flash` declaration; whether a runtime per-call `Model` override parameter is honored by all CLI/Desktop versions is not explicitly specified in the public Hooks schema, so rely on the agent frontmatter rather than passing `Model` in the call payload.)*

### Parallel Review Lanes
When a draft is ready for review, `muse` spawns multiple review lanes concurrently in a single tool call:

```json
{
  "Subagents": [
    {
      "TypeName": "critic",
      "Role": "Adversarial Draft Critic",
      "Prompt": "Diagnose chapter 3 draft at work/drafts/ch03.md for emotional pacing and narrative tension. Return anchored findings.",
      "Workspace": "inherit"
    },
    {
      "TypeName": "continuity-checker",
      "Role": "Canon Continuity Auditor",
      "Prompt": "Cross-reference chapter 3 draft at work/drafts/ch03.md against kb/timeline/timeline.md and kb/characters/alyssa.md. Flag any chronological or state contradictions.",
      "Workspace": "inherit"
    },
    {
      "TypeName": "reader-sim",
      "Role": "Experiential Reader Reaction",
      "Prompt": "Perform an experiential cold read of work/drafts/ch03.md as a first-time fantasy reader. Record moment-by-moment emotional turns and confusions.",
      "Workspace": "inherit"
    }
  ]
}
```

---

## 4. Multi-Turn Stateful Iteration vs. Fresh Cold Reads

### A. Stateful Producer Iteration (`writer`)
- The `writer` subagent maintains conversation history and context while in the `idle` state.
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

`muse` delegates knowledge base curation to `kb-lead`:
1. `muse` invokes `kb-lead`:
   ```json
   {
     "Subagents": [
       {
         "TypeName": "kb-lead",
         "Role": "KB Lead: Chapter 3 Capture",
         "Prompt": "Update the knowledge base following completion of Chapter 3. Extract newly confirmed facts about the citadel into kb/world/locations.md.",
         "Workspace": "inherit"
       }
     ]
   }
   ```
2. `kb-lead` is equipped with `invoke_subagent`, `manage_subagents`, and `send_message` (up to Antigravity's 10-level nesting limit) to spawn `session-miner`, `explorer`, `cold-reader`, and `kb-maintainer`, and commits the updated knowledge base tree.

---

## 6. Lifecycle Management with `manage_subagents`

Manage active background subagents when needed:
- **`list`**: Enumerate all active direct subagents with their conversation IDs and lifecycle state (`running`, `idle`, etc.).
- **`kill`**: Terminate specific subagents by passing `ConversationIds` when a lane is cancelled or superseded.
- **`kill_all`**: Cleanly terminate all active subagents and their descendants.

Subagents report their results asynchronously back to the calling agent. Allow subagents to finish and synthesize the aggregated findings before presenting prioritized choices to the author.
