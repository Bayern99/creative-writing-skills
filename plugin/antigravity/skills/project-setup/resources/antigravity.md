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
agy plugin install https://github.com/Bayern99/creative-writing-skills/tree/antigravity-plugin/plugin/antigravity
```

Verify installation:
```bash
agy plugin list
agy agents
```
You will see `creative-writing-skills` enabled with its 15 agents and 27 skills.

### Via Antigravity Desktop App

Place the complete `plugin/antigravity/` directory at `~/.gemini/config/plugins/creative-writing-skills/` for all workspaces, or at `.agents/plugins/creative-writing-skills/` within one project. Replace the whole installed plugin directory when updating a manual installation, so removed skills do not remain. Open **Customizations > Installed** from the left sidebar to inspect and enable the plugin. See the [official plugin guide](https://antigravity.google/docs/plugins).

---

## Agent Setup & Starting a Session

### Selecting Your Main Agent
In Antigravity, four primary entry points are exposed in the Agent dropdown:
- **`muse` (Recommended)**: Your collaborative creative partner. Coordinates 14 specialist subagents, leads planning and drafting, and owns the verdict on drafts. Uses your session model selection.
- **`writer`**: Standalone production prose writer for quick drafting or revisions.
- **`character-sim`**: Interactive in-character conversational partner for voice discovery.
- **`outliner`**: Dedicated story architect for outline generation.

Choose any available main-session model in the picker. The intended allocation is fixed Hydrogen for `writer`, `critic`, `outliner`, `style-creator`, and `kb-lead`, and fixed Flash for the other nine specialists, independently of your main model. When you select writer, character-sim, or outliner directly as the primary agent, choose that session's model in the picker too.

The current ordinary native configuration uses `model: flash` for all 14 children as an explicit interim. The [documented tiers](https://antigravity.google/docs/build-plugins) do not support an independent concrete Hydrogen selection; see [issue #1270](https://github.com/google-antigravity/antigravity-cli/issues/1270). A task requiring Hydrogen must be reported as blocked before dispatch, with Flash used only if the author accepts it. No child inherits the main model.

Official [Swarm](https://antigravity.google/docs/swarm) can select worker models independently, but this plugin has no Swarm integration. The workflow below uses ordinary native subagents.

To launch in CLI:
```bash
agy --agent muse
```
Or in Desktop App, select **muse** from the agent selector.

### Viewing Subagent Progress

For clickable child conversations, choose **Settings > General > Interface Layout > Software Engineering** and open the **Overview** panel at the conversation's top right. Select a child under **Subagents** to open its conversation in the side panel. **Knowledge Work** layout condenses subagent cards and tool calls into a live progress line. Switching layouts applies immediately. See [Interface Layout](https://antigravity.google/docs/settings) and [Side panel and Overview](https://antigravity.google/docs/side-panel/).

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
   `muse` reviews `AGENTS.md` and current character states in `kb/`, then plans with you. It can delegate a separate structural pass to `outliner`.

2. **Draft**:
   Collaborate with `muse` on prose in its own context, or delegate a fresh draft, revision, alternate take, polish pass, or long draft to `writer`; pass the style guides in `kb/styles/` and ask it to report judgment calls to `muse`.

3. **Review**:
   `muse` invokes specialized reviewer subagents concurrently via `invoke_subagent`:
   - **`critic`**: Evaluates narrative tension, character voice, and prose cadence.
   - **`continuity-checker`**: Flags contradictions against facts in `kb/` and timeline events.
   - **`reader-sim`**: Provides emotional, moment-by-moment feedback from the reader's perspective.

4. **Revise**:
   `muse` synthesizes reviewer findings, helps you prioritize the highest-impact fixes, and revises with you or the existing `writer` instance. After two critique rounds on a chapter, it presents remaining concerns for your decision.

5. **Knowledge Capture**:
   Once a chapter or ruling settles, `muse` briefs `kb-lead` with what settled and the supporting files. `kb-lead` updates knowledge, deletes stale content, and reorganizes affected pages. Trial directions stay marked as trials.
