# Creative Writing Skills · Codex 插件

把插件装一次，然后在自己的小说项目里开 Codex 会话。可以从一句梗概、一段试写或已有的长篇开始。插件自带写作参考资料，安装时无需连接外部应用。

## 从 GitHub 安装

在任意目录用支持 `codex plugin` 的 Codex CLI 运行以下命令。第一条注册提供 Codex 适配的分支，第二条安装插件。

```sh
codex plugin marketplace add Bayern99/creative-writing-skills --ref codex-plugin
codex plugin add creative-writing-skills@creative-writing-skills
```

如果以前装过旧名称下的插件，请先运行下面两条命令，再按上方步骤安装，避免同时加载两份技能。只注册过旧插件源的用户可以直接运行第二条。

```sh
codex plugin remove creative-writing-skills@bayern-writing
codex plugin marketplace remove bayern-writing
```

打开自己的小说项目，新建 Codex 会话。在技能选择器中输入 `$`，选择下列技能之一。插件目录里的来源名为 **Creative Writing Skills**。

| 入口 | 可以直接试的话 |
| --- | --- |
| `creative-writing-muse` | “续写我贴的这段渡口戏。保持阿芸的视角，让她发现少了一个人，别揭晓是谁。先在聊天里试写。” |
| `project-setup` | “帮我设置这部长篇。正稿放在‘正文’，试稿放在‘试写’。先给我看准备补充的项目约定。” |
| `story-review` | “当第一次读到第三章的读者。指出你从哪句话开始怀疑哥哥在撒谎，先别改稿。” |
| `story-memory` | “第三章已经定稿。把钥匙最后由谁保管更新到人物页，附上场景出处。备选结局仍放在工作笔记里。” |

在聊天中直接试稿可以跳过项目初始化。设置项目时，插件先展示拟建的目录和约定，经作者确认后落盘。

## Muse 怎么用子代理

在小说项目里显式选 `$creative-writing-muse`。可以直接说：“第一章是定稿。请给第二章做一次独立的跨章连续性核查，也单独看看线索递给读者时会不会太早。我只要审稿，附一句你实际怎么分工的。” Muse 在当前会话执笔和裁决，按任务给通用子代理交代角色、可见材料和交付物。写短段或说“这次你自己看”时，留在当前会话就能完成。

四个入口都需要显式选用。安装登记插件源和插件启用状态。全局模型、权限、审批、并发上限和项目的 `.codex/` 沿用现有设置；单个任务的模型和推理强度按角色定义与宿主实际能力选择。宿主无法委派时，Muse 会说明哪些工作由同一会话分次完成。首次试读的材料边界由简报和独立上下文控制；受托子代理继承当前工作区的文件权限。

**指定模型时可以这样要求：**“按上游 critic 的 Opus / high 审稿。如果这个环境无法运行，请告诉我；等我决定是否接受替代。”原生 Codex 使用当前宿主提供的模型。已经配置上游 Claude Code 或 Meridian 的项目，可以在对应运行时调用其具名角色，由该运行时执行模型路由和工具限制。严格复现跨模型家族的复核需要实际运行两个提供商。

| 角色 | Meridian 源定义 | 上游 Claude Code 构建 |
| --- | --- | --- |
| writer | opus，匹配 opus 时 high | opus / high |
| critic | opus / high | opus / high |
| continuity-checker | sonnet / high | sonnet / high |
| creative-researcher | luna / medium | sonnet / medium |
| kb-lead | opus / medium | opus / medium |

完整原文位于[角色源定义](plugins/creative-writing-skills/reference/agents)和[Claude 构建定义](plugins/creative-writing-skills/reference/claude-agents)。角色支持的工具、可用技能、模型策略及匹配时的覆盖值以对应文件为准。

上游分工、Codex 映射、一次真实的子代理运行和可复用的两章样本见[工作流验证记录](docs/codex-workflow/README.md)。

## 从 GitHub 更新

```sh
codex plugin marketplace upgrade creative-writing-skills
codex plugin add creative-writing-skills@creative-writing-skills
```

新开会话后即可使用。运行 `codex plugin list --marketplace creative-writing-skills` 可查看安装状态。

## 本地安装与打包

独立包位于 `plugins/creative-writing-skills/`，源目录可以直接编辑。本地目录清单是 `.agents/plugins/marketplace.json`。插件名、作者、项目主页、许可证和版本与上游项目元数据对齐。更新上游基线时同步 `plugin.json`，提交后在仓库根目录打包：

```sh
git archive --format=zip --prefix=creative-writing-codex/ -o creative-writing-codex.zip HEAD .agents/plugins/marketplace.json plugins/creative-writing-skills CODEX.zh-CN.md docs/codex-workflow
```

从 ZIP 或本地检出安装时，在包含本说明和 `.agents/` 的目录运行 `codex plugin marketplace add .`，再运行 `codex plugin add creative-writing-skills@creative-writing-skills`。

本版基于 Jimmy Yao 的 Creative Writing Skills 0.9.5（Apache-2.0）。仓库维护者更新上游基线后，运行 `python3 scripts/sync_codex_references.py`，再运行同一命令加 `--check` 验证安装包中的参考文件。脚本从源码、已提交的 Mars 构建产物和其锁定的 meridian-base 版本生成；已有该依赖的 Git 检出时，可以通过 `--meridian-base PATH` 离线构建。使用插件时所有资料均在安装包内。独立的 writing-sync 工具继续由原依赖提供。
