# Codex model defaults for the writing roles

Use the original Meridian role's default as the starting point. Opus maps to Astra, Sonnet maps to Sol, and roles already using Terra or Luna keep those families. Carry over the source role's reasoning effort, including a matching override. For `kb-lead` use its explicit Astra override. A blank effort uses the selected model's default.

| Role | Upstream default | Codex model ID | Codex effort |
| --- | --- | --- | --- |
| muse | opus | `gpt-6.2-astra` | |
| brainstormer | opus | `gpt-6.2-astra` | |
| character-sim | opus | `gpt-6.2-astra` | |
| critic | opus / high | `gpt-6.2-astra` | high |
| reader-sim | opus | `gpt-6.2-astra` | |
| style-creator | opus / high | `gpt-6.2-astra` | high |
| writer | opus / high | `gpt-6.2-astra` | high |
| kb-lead | opus / medium | `gpt-6.2-astra` | high |
| continuity-checker | sonnet / high | `gpt-6.2-sol` | high |
| outliner | sonnet | `gpt-6.2-sol` | |
| setup | sonnet / low | `gpt-6.2-sol` | low |
| spark | sonnet / medium | `gpt-6.2-sol` | medium |
| cold-reader | terra / medium | `gpt-6.1-terra` | medium |
| kb-maintainer | terra / medium | `gpt-6.1-terra` | medium |
| session-miner | terra / medium | `gpt-6.1-terra` | medium |
| creative-researcher | luna / medium | `gpt-6-luna` | medium |
| explorer | luna / medium | `gpt-6-luna` | medium |

For subagents, pass the model ID in the spawn tool's model field and any supported effort in its reasoning-effort field. Where the tool requires a fresh context for overrides, start one and send the role brief with the relevant sources. When no explicit effort is listed for the role, omit the effort field. If the client exposes a model catalog, check it first. An availability or capability error can be retried once with the host's defaults unless the author required the model for that task. If the host exposes no model-selection field, use its configured subagent and explain any material difference.

Muse, Spark, and Setup are entry roles in the author's session. The table gives their recommended selection in the composer or with `codex -m`. A skill uses the session's selected model for the turn.
