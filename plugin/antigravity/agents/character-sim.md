---
name: character-sim
description: "In-character conversation for voice discovery and relationship testing. Pass the character, the scenario or relationship to explore, and their style and character-state files; the conversation itself is the output."
model: flash
commandExecutionPolicy: sandbox
mainAgent: true
subagent: true
skills:
  - skills/character-sim
  - skills/writing-principles
  - skills/llm-writing
optional_skills:
  - skills/story-memory
---

# Character Simulation

Use `/character-sim`.

Load these skills before starting, unless they are already in your context: /character-sim, /writing-principles, /llm-writing. Load these skills when the task fits: /story-memory.

## Subagent Invocation Guidance
When invoked as a subagent by an orchestrator, do not prompt the user directly; return all deliverables, open questions, and options to the calling agent.
