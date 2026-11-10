# Antigravity 2.0 Setup & Workflow Guide

This guide details how to install, configure, and use the `creative-writing-skills` plugin in Google Antigravity 2.0 (Desktop App and CLI).

## Installation

### Via Antigravity CLI
Install from a local path:
```bash
agy plugin install /path/to/creative-writing-skills/plugin/antigravity
```

Or install directly from the GitHub repository tree URL:
```bash
agy plugin install https://github.com/haowjy/creative-writing-skills/tree/main/plugin/antigravity
```

Verify installation:
```bash
agy plugin list
agy agents
```
You will see `creative-writing-skills` enabled with its 15 agents and 28 skills.

### Via Antigravity Desktop App
1. Open Antigravity Settings -> **Plugins**.
2. Select **Install Plugin** and provide the repository URL or local plugin directory.
3. Verify that the plugin appears enabled with the quill logo.

---

## Agent Setup & Starting a Session

### Selecting Your Main Agent
In Antigravity, four primary entry points are exposed in the Agent dropdown:
- **`muse` (Recommended)**: The orchestrator and your collaborative creative partner. Coordinates all 13 specialized subagents, leads planning, and owns the verdict on drafts. Runs with `model: inherit`, honoring your session model selection.
- **`writer`**: Standalone production prose writer for quick drafting or revisions.
- **`character-sim`**: Interactive in-character conversational partner for voice discovery.
- **`outliner`**: Dedicated story architect for outline generation.

All remaining subagents (`critic`, `reader-sim`, `continuity-checker`, etc.) run on `model: flash` and are spawned dynamically by `muse`.

To launch in CLI:
```bash
agy --agent muse
```
Or in Desktop App, select **muse** from the top agent selector.

---

## First Session: Project Setup

1. In your project workspace, run:
   ```text
   /project-setup
   ```
   *(Note: `/project-setup` is author-invoked and guides you through an initial creative interview).*

2. The interview helps establish:
   - **`AGENTS.md`**: Project overview, active storylines, genre rules, and voice principles.
   - **`kb/` Layout**:
     - `kb/characters/`: Character profiles and relationship sheets.
     - `kb/world/`: Canon lore, geography, rules of the world.
     - `kb/timeline/`: Chronological sequence of events.
     - `kb/styles/`: Voice guides and prose samples.
   - **`work/` Directory**: Transient working files for brainstorms, outlines, and critiques.

3. Commit the initial structure with git:
   ```bash
   git add AGENTS.md kb/
   git commit -m "Initialize story project structure"
   ```

---

## Story Workflow: Writing a Chapter

1. **Plan**:
   Ask `muse`: *"Let's plan Chapter 4."*
   `muse` reviews `AGENTS.md` and current character states in `kb/`, then invokes `outliner` to generate structured scene beats in `work/outlines/ch04.md`.

2. **Draft**:
   Collaborate with `muse` on prose, or ask `muse` to invoke `writer` to produce a fresh draft:
   `writer` drafts the scene strictly following the style guides in `kb/styles/` and reports judgment calls back to `muse`.

3. **Review**:
   `muse` invokes specialized reviewer subagents concurrently via `invoke_subagent`:
   - **`critic`**: Evaluates narrative tension, character voice, and prose cadence.
   - **`continuity-checker`**: Flags contradictions against facts in `kb/` and timeline events.
   - **`reader-sim`**: Provides emotional, moment-by-moment feedback from the reader's perspective.

4. **Revise**:
   `muse` synthesizes reviewer findings, helps you prioritize the highest-impact fixes, and updates the prose with `writer`.

5. **Knowledge Capture**:
   Once the chapter is accepted, `muse` invokes `kb-lead` to extract durable decisions and update character sheets in `kb/`.
