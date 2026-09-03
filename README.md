# 派星文案检查 Skill

给合生元派星小红书文案做词表检查、事实核查、定点修正、场景化和口语化。适用于 Codex、Claude Code 等支持 Agent Skills 的工具。

中文显示名称：**派星文案检查**。安装和调用名称：`paixing-copy-review`。

## 安装前

- 仓库公开，任何人都可以查看和安装，无需协作者邀请或登录 GitHub。
- 本机需要能运行 Python 3；检查脚本只使用标准库，不需要安装 Python 依赖。
- 完整改稿需要在 AI 工具中使用。单独运行 Python 脚本只会完成词表检查或改动范围验证。

## 安装到 Codex

在 Codex 中发送下面这句话：

```text
请使用 skill-installer 安装这个 GitHub skill：
https://github.com/gizzap/paixing-copy-skill/tree/main/skills/paixing-copy-review
```

直接发送上面的安装链接即可，无需配置 GitHub 令牌。

## 用命令安装到 Codex 或 Claude Code

需要 Node.js、npm 和 Git。以下命令使用现成的 [Skills CLI](https://github.com/vercel-labs/skills)，按自己的工具选择一条即可：

**Codex：**

```bash
npx skills add gizzap/paixing-copy-skill --skill paixing-copy-review --agent codex --global
```

**Claude Code：**

```bash
npx skills add gizzap/paixing-copy-skill --skill paixing-copy-review --agent claude-code --global
```

`--global` 表示安装后可以在不同项目里使用；只想给当前项目使用，去掉它即可。

安装后开启新对话验证。Codex 输入 `$paixing-copy-review`，Claude Code 输入 `/paixing-copy-review`；都可以直接用中文说「用派星文案检查 skill 帮我改这篇稿子」。Claude Code 的技能目录与调用方式见[官方说明](https://code.claude.com/docs/zh-CN/skills)。

若已有旧的「派星文案检查」版本，请先确认新版本可用，再移走旧目录，避免同时触发两份规则；旧版自定义词表先保留备份。

## 不用命令安装

在 GitHub 仓库页面选择 **Code → Download ZIP**，解压后找到 `skills/paixing-copy-review`，将这个完整文件夹复制到所用工具的技能目录：

| 工具 | 位置 |
|---|---|
| Codex | `~/.codex/skills/paixing-copy-review`；设置了 `CODEX_HOME` 时使用其下的 `skills/` |
| Claude Code | `~/.claude/skills/paixing-copy-review` |

`~` 表示用户主目录。不要只复制 `SKILL.md`，脚本、提示词和词表都需要一起安装。

## 怎么用

把稿件放入 AI 工具可读取的工作目录，然后发送：

```text
请用派星文案检查 skill 检查并修改这篇稿子。
正文和评论区一起检查，保留原稿，另存改稿、修改清单和需要确认的事项。
```

批量 CSV：

```text
请用派星文案检查 skill 处理这份 CSV 的「初稿」列。
保留原列，另外输出改稿、问题清单和待确认项。
```

当前规则围绕派星 2 段文案设置。项目人群、段位、竞品口径和核心信息变化时，应先同步对应规则。

## 验证安装文件

下面命令在下载或克隆的仓库根目录执行，使用的两份示例均为合成文本：

```bash
python3 skills/paixing-copy-review/check.py skills/paixing-copy-review/examples/示例稿.txt --json
```

预期出现一条竞品表述提示：将「皇家美素佳儿」统一为「皇美」。验证修正后的文本：

```bash
python3 skills/paixing-copy-review/check.py skills/paixing-copy-review/examples/修正后.txt --json
```

预期输出 `{}`。Windows 可将 `python3` 换成 `py -3`。

实际使用时，脚本路径相对于 skill 安装目录；稿件可在任意工作目录。需要运行 `verify.py` 时，按 `SKILL.md` 提供原稿、定点修正稿及完整问题清单；该脚本验证定点修正范围，不能用于判定整篇自由润色的质量。

## 更新

使用 Skills CLI 安装的同事，重新运行上面的安装命令即可拉取并安装仓库当前版本；覆盖前先备份自己修改过的词表。使用其他方式安装的，获取新版完整文件夹后替换旧版。

维护者在本仓库的 `skills/paixing-copy-review/` 内修改规则，提交并推送到 `main`。本机其他目录里的同名 skill 不会自动同步到 GitHub。

| 目录或文件 | 用途 |
|---|---|
| `SKILL.md` | 完整改稿流程与边界 |
| `check.py` / `verify.py` | 词表检查 / 定点修正范围验证 |
| `prompts/` | 各阶段提示词和通用约束 |
| `tables/` | 红线词、卡审词、竞品、策略、参考数据及素材 |
| `agents/openai.yaml` | Codex 中文显示名称与示例指令 |
| `examples/` | 合成的安装验证样例 |
| `失败记录.md` | 原开发过程的经验记录 |

此分发版来自项目目录的 skill，未收录真实客户稿件、40 篇回归集及实验产物。原文中的历史评测数字不是当前版本的复测结果。

词表保留原有规则与备注：月龄参考和效果周期仍有待业务确认的估值，场景素材库当前为空；红线词和卡审词中的 `S01` 等来源编号未附原始来源对照表，不应将编号本身当作已核验证据。遇到需要核验的条目，按其处理建议和实际业务资料判断。
