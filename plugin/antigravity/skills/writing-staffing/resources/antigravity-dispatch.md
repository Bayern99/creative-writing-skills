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

All 14 subagents are configured to `model: flash` (Gemini 3.8 Flash):
- **Why**: Gemini 3.8 Flash provides fast, cost-effective, high-throughput execution across parallel lanes.
- **Differentiation**: Instead of relying on disparate third-party model families, lane independence is achieved through:
  1. Distinct system instructions and craft principles.
  2. Targeted skill bundles (e.g., `md-validation` for `continuity-checker`, `reader-sim` for naive reaction).
  3. Strict behavioral contracts (read-only for reviewers; no direct user prompt for subagents).
- **Muse**: Inherits the author's primary conversation model (`model: inherit`), allowing authors to choose their preferred model in the Antigravity Desktop App or CLI.

---

## 3. Dispatching Subagents with `invoke_subagent`

### Parallel Review Lanes
When a draft is ready for review, `muse` spawns multiple review lanes in a single invocation to run concurrently:

```json
{
  "subagents": [
    {
      "agentName": "critic",
      "instruction": "Diagnose chapter 3 draft at work/drafts/ch03.md for emotional pacing and narrative tension. Return anchored findings.",
      "title": "Critic: Tension and Pacing"
    },
    {
      "agentName": "continuity-checker",
      "instruction": "Cross-reference chapter 3 draft at work/drafts/ch03.md against kb/timeline/timeline.md and kb/characters/alyssa.md. Flag any chronological or state contradictions.",
      "title": "Continuity: Alyssa State & Timeline"
    },
    {
      "agentName": "reader-sim",
      "instruction": "Perform an experiential cold read of work/drafts/ch03.md as a first-time fantasy reader. Record moment-by-moment emotional turns and confusions.",
      "title": "Reader Sim: First Read"
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
     "subagents": [
       {
         "agentName": "kb-lead",
         "instruction": "Update the knowledge base following completion of Chapter 3. Extract newly confirmed facts about the citadel into kb/world/locations.md.",
         "title": "KB Lead: Chapter 3 Capture"
       }
     ]
   }
   ```
2. `kb-lead` in turn invokes `session-miner` to inspect conversation transcripts or `explorer` to check references, and applies clean updates to `kb/`.

---

## 6. Lifecycle Management with `manage_subagents`

Monitor and clean up running subagents:
- **`list`**: View all active and completed subagent conversations.
- **`status`**: Check execution status and retrieve output logs.
- **`kill`**: Terminate runaway or stuck subagents.

Always allow subagents to finish and report results cleanly before synthesizing next steps for the author.
