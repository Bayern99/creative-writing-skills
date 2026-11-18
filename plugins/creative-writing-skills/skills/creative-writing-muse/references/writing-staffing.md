# Writing staffing in Codex

This file adapts how Codex runs the original workflow. Use the [story workflow](../../../reference/skills/story-workflow/SKILL.md) to choose the next step and the [staffing skill](../../../reference/skills/writing-staffing/SKILL.md) to choose the role. Read its [producer](../../../reference/skills/writing-staffing/resources/producers.md) or [reviewer](../../../reference/skills/writing-staffing/resources/reviewers.md) guidance for the assignment.

## Start with the current session

The current Codex session is Muse. Astra is the recommended session model. Use the selected model to work with the author, draft ordinary scenes, and decide what to do with reports. Spark is the single-session choice when the author wants a lightweight pass. Project setup runs in the current session when the author starts it.

For work that needs an independent perspective, launch a native Codex subagent when the session provides that tool and permits delegation. Explicitly selecting Muse for that work is enough unless the host has its own delegation requirement. Use the general-purpose subagent with a role name in the brief. Use focused, read-only exploration for repository searches and continuity investigation where the host offers it. Resolve the installed plugin directory before sending a brief. Give the worker the absolute path to `reference/agents/<role>.md`, the relevant upstream skills under `reference/skills/`, the draft version, and the one question to answer. Apply the role's responsibilities, skill requirements and boundaries. Treat its model aliases, launcher commands, and tool declarations as input to the Codex adaptation below.

## Choose from available Codex models and tools

- **Default.** Read the [Codex role-to-model table](codex-models.md) before launching a subagent. Pass the applicable model ID and any listed reasoning effort as actual tool parameters. If a mapped model or effort is unavailable, use the table's recovery path.
- **Model request.** An explicit author request or a project-configured mapping takes precedence. Treat a required model or provider as a constraint on that assignment. If unavailable, identify what is blocked and continue the rest.
- **Independent review.** For a pivotal or disputed scene, use separate briefs that challenge different assumptions. When two model families are actually available and suitable, run the same question across both as upstream describes. If only one family is available, finish the review through independent contexts and report that scope when it matters. If isolation is unavailable, label the trial as a simulated reading with prior context.
- **Tools.** Use the current workspace's file tools for manuscript work and the current search or connectors for research. Reviewers and simulated readers report findings. Name the only path the writer may edit. Follow the host's permissions. The upstream tool and approval declarations describe the original environment. If a required restriction cannot be enforced, surface that limit. When source access is missing, use provided material and identify facts that still need checking.

Configured Claude Code and Meridian workflows can use the corresponding upstream profiles when the author explicitly chooses that runtime. The original definitions are under `reference/agents/`, and the Claude build is under `reference/claude-agents/`.

## Run the handoff

Follow the [context brief](../../../reference/skills/story-memory/resources/story-context.md). Give each worker the minimum needed chapters, decisions, and canon. Supply only reader-visible pages to a first-time reader in a fresh context. Assign one writer per scene. Run independent passes in parallel within the host's capacity, wait for their answers, and close completed workers when more capacity is needed. If native delegation is unavailable or a worker cannot finish, use the upstream single-session method for the remaining ordinary tasks, and say when a pass lacked independent context.

Muse checks the findings and takes the next authorized step. A review-only request ends with findings. Use the upstream two-round revision limit, then let the author choose. Give kb-lead settled decisions and their source pages. Keep provisional material in the work area. Wrap up in terms of the story. Mention which roles ran and any limitations that affected the result.
