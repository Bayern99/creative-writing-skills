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

- **Main session**: The author selects the model for `muse` in Antigravity's model picker. Choose any available main model; **Gemini 4 Hydrogen** is one example that produces a Hydrogen + Flash combination.
- **Inherited specialists**: `writer`, `critic`, `outliner`, `style-creator`, and `kb-lead` use `model: inherit` for prose, critique, structure, voice, and knowledge judgments.
- **Flash specialists**: `brainstormer`, `character-sim`, `continuity-checker`, `reader-sim`, `creative-researcher`, `explorer`, `session-miner`, `cold-reader`, and `kb-maintainer` use `model: flash`.

`inherit` selects the calling agent's model; it is not an independent Hydrogen pin. Changing the main model changes the inherited specialists too. Flash currently resolves to Gemini 3.8 Flash. Inspect the resolved child model when verifying a run, and report the observed model rather than inferring it from the role name. See [plugin model tiers](https://antigravity.google/docs/build-plugins) and [model selection](https://antigravity.google/docs/models).

---

## 3. Dispatching Subagents with `invoke_subagent`

### Native Call Schema
Per the official Antigravity Hooks and Subagents documentation, `invoke_subagent` accepts a `Subagents` array where each entry defines `TypeName`, `Role`, `Prompt`, and optional `Workspace` (`inherit`, `branch`, or `share`).
Use each bundled agent's `model: inherit` or `model: flash` frontmatter for the role allocation above. The examples use the fields documented in the [Hooks reference](https://antigravity.google/docs/hooks). Follow the active runtime's tool schema for any additional parameters; keep model slugs out of these tier-based examples.

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

## 7. Visible Progress

Keep delegation on native `invoke_subagent` sessions so the author can open each child conversation. After dispatch, identify the role and returned conversation ID; when a child reports a milestone or blocker, summarize that observed update. Use `send_message` for follow-up instructions to an existing child.

The App's **Knowledge Work** layout hides subagent cards behind a progress line. To inspect child conversations, use **Settings > General > Interface Layout > Software Engineering**, then open the **Overview** panel at the conversation's top right and select a child under **Subagents**. Its conversation opens in the side panel. **See all** includes completed children. See [Interface Layout](https://antigravity.google/docs/settings) and [Subagent monitoring](https://antigravity.google/docs/subagents).
