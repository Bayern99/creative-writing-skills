# 在 Codex 中执行上游分工

**先确定任务的运行方式。** 当前对话显式启用 Muse 后，在这里与作者交流、判断和执笔。依照[上游生命周期](../../../reference/skills/story-workflow/SKILL.md)和[分工方法](../../../reference/skills/writing-staffing/SKILL.md)决定这一步需不需要子代理。需要时，先读[生产角色](../../../reference/skills/writing-staffing/resources/producers.md)或[审读角色](../../../reference/skills/writing-staffing/resources/reviewers.md)。轻量单人协作参照 spark，主动初始化参照 setup；两者都是没有下属的主角色。

**给角色正确的定义。** 下文的路径以已安装插件的根目录为起点，交接时转为绝对路径。打开 `reference/agents/<角色>.md`，读取其正文，以及 model、effort、model-policies、skills、tools、subagents 等实际存在的字段。以它列出的下属和工作边界为准。其中五个依赖角色（含 kb-lead）的原始定义取自上游锁定的 meridian-base。对照 Claude Code 时，读上游编译后的 `reference/claude-agents/<角色>.md`。运行时用哪种定义就报告哪种。

**模型选择必须有依据。** 原生 Codex 优先使用当前工具确实支持、且有明确映射的角色默认模型；按实际选中的别名读取对应的 policy override，并使用工具确实支持的 effort。未指定 effort 时保留宿主设置。model-policies 描述匹配条件；不要把列表顺序臆解成切换模型的先后。具体模型 ID 或别名映射须来自当前宿主目录或作者配置。不要凭名称相似猜测，也不要把别名直接当作跨供应商 API 的模型 ID。

- 作者要求指定模型、独立供应商或严格复现时，先核实角色、模型和工具都可用。无法满足时说清卡在哪个角色和能力，将这项留待具备条件的运行时执行。遇到匹配的 no-fallback 策略时同样保留这一限制。
- 普通 Codex 写作中，原模型不可用且用户接受 Codex 模型协作时，可以用宿主可用的子代理承担原分工；首次替代时点明原模型与实际选择（宿主未回报具体型号就说未回报）。对不同视角用不同简报。上游要求跨模型家族复核时，要取得两家实际运行的结果才算完成。
- 当作者已选择并配置上游运行时时，把工作交给那个运行时解析具名角色。Claude Code 使用已安装插件的具名 agent；Meridian 使用项目已安装的 profile，可先以 `meridian --json spawn -a critic -p 'Review routing' --dry-run` 查看该角色将选的 harness、model 和权限，再用实际简报运行。若作者要求精确型号，核对 dry-run 选中的具体模型、提供商和 effort；实际执行后再核对运行回执。dry-run 只证明路由。外部运行须处在作者已允许的模型、文件和权限范围内。
- 当前会话扮演 Muse 或 Spark 也遵循相同的模型披露原则。安装和写作均保留用户现有配置。上游的 sandbox、approval、工具列表用于识别运行差异；角色文件不能提高当前权限。若工具限制是硬性要求而宿主不能隔离该工具，明确告知，不能将文字简报描述成强制隔离。

**执行和验收。** 需要独立判断时使用当前宿主的子代理工具。简报给出角色定义、选定的稿本、唯一任务、可读材料、交付格式和允许的写入范围。角色的 skills.load（或 skills 列表）按其定义加载；skills.available 按任务使用。将 `/name`、`/creative-writing-skills:name` 解析到 `reference/skills/name/SKILL.md`，各个 resources 路径相对于该技能目录。多角色共享同一份稿件，但每个场景只有一个执笔人。只读角色在简报中明确禁止写入；核实支持的工具和权限。研究需要可用来源，无法查证就标缺口。

遵循[上下文交接](../../../reference/skills/story-memory/resources/story-context.md)。首次试读只给读者当时能读到的正文，另开不继承编辑讨论的上下文。等独立报告全部回来，Muse 核对、修订，再试读；每章至多两轮评读加修订。定稿依据交给 kb-lead。若作者选择单人协作，按上游生命周期的单会话路径逐项处理。向作者报告实际角色、实用模型（若可见）、已完成和缺失的复核。
