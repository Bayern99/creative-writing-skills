# Creative Writing Skills · Codex 自用版

把插件装一次，然后在自己的小说项目里开 Codex 会话。可以从一句梗概、一段试写或已有的长篇开始。插件自带写作参考资料，安装时无需连接外部应用。

## 安装

将整个 ZIP 解压到准备长期保留的位置。在包含本说明和 `.agents/` 的目录打开终端，运行以下命令。使用支持 `codex plugin` 的 Codex CLI。

```sh
codex plugin marketplace add .
codex plugin add creative-writing-skills@bayern-writing
codex plugin list --marketplace bayern-writing
```

从本地 Git 分支使用时也可以在仓库根目录运行这三条命令。打开自己的小说项目，新建 Codex 会话。在技能选择器中输入 `$`，选择下列技能之一。如果桌面端已经打开，重启后再看插件目录，来源名为 **Bayern · 写作工具**。

| 入口 | 可以直接试的话 |
| --- | --- |
| `creative-writing-muse` | “续写我贴的这段渡口戏。保持阿芸的视角，让她发现少了一个人，别揭晓是谁。先在聊天里试写。” |
| `project-setup` | “帮我设置这部长篇。正稿放在‘正文’，试稿放在‘试写’。先给我看准备补充的项目约定。” |
| `story-review` | “当第一次读到第三章的读者。指出你从哪句话开始怀疑哥哥在撒谎，先别改稿。” |
| `story-memory` | “第三章已经定稿。把钥匙最后由谁保管更新到人物页，附上场景出处。备选结局仍放在工作笔记里。” |

在聊天中直接试稿可以跳过项目初始化。设置项目时，插件先展示拟建的目录和约定，经作者确认后落盘。

## 打包和维护

独立包位于 `plugins/creative-writing-skills/`，源目录可以直接编辑。本地目录清单是 `.agents/plugins/marketplace.json`。发新版时更新插件自己的 `plugin.json` 版本号，提交后在仓库根目录打包：

```sh
git archive --format=zip --prefix=creative-writing-codex/ -o creative-writing-codex.zip HEAD .agents/plugins/marketplace.json plugins/creative-writing-skills CODEX.zh-CN.md
```

更新自用安装时，把新版解压到原来的插件源位置，再运行安装命令并新建会话。

本版基于 Jimmy Yao 的 Creative Writing Skills 0.9.5（Apache-2.0）。随包的三篇英文参考资料保留原文。同步上游时，可把 `skills/creative-writing-craft/resources/` 里的 `prose-writing.md` 和 `style-analysis.md` 更新到 Muse 的 `references/`，把 `skills/story-review/resources/editorial-review.md` 更新到审稿技能的 `references/`。许可证在包内的 `LICENSE`。
