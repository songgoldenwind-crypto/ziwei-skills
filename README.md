# 紫微斗数 Agent Skills（全平台版）

面向各类 AI Agent 的紫微斗数排盘、命盘核对与分层断盘能力包，基于 [Agent Skills](https://agentskills.io/) 开放格式构建。ChatGPT、Claude、Codex、WorkBuddy、Cursor、Gemini、GitHub Copilot、OpenCode、Windsurf、Cline 及其他兼容客户端共用同一套技能规则，各平台元数据和引用语法由安装器与打包脚本生成。

## 包含内容

| 目录 | 用途 |
| --- | --- |
| `skills/ziwei/` | 紫微斗数分层断盘：核盘、格局、正曜组合、四化、大限流年与专题判断 |
| `ziwei-paipan-code/` | 真太阳时校正、本命盘与运限盘，输出 JSON |

排盘只生成盘面结构。吉凶判断由 `ziwei` Skill 的规则执行，不把排盘字段直接写成命运事实。

## 兼容范围

本仓库同时覆盖本地 Agent、IDE Agent、云端对话产品、插件市场和 Skills API。没有列出的兼容客户端也可通过开放标准目录或自定义安装目录使用。

| Agent / 渠道 | 用户级目录或分发方式 | 项目级目录 |
| --- | --- | --- |
| 通用 Agent Skills 客户端 | `~/.agents/skills` 或自定义目录 | `.agents/skills` |
| Codex CLI、App、Cloud、IDE | `~/.agents/skills` | `.agents/skills` |
| ChatGPT 网页、桌面、移动端 | Skill 上传 / OpenAI 插件 / 工作区 GitHub 市场 | — |
| Claude Code、Claude Agent SDK | `~/.claude/skills` 或 Claude 插件市场 | `.claude/skills` |
| Claude 网页、桌面端、Cowork | 在 `Customize > Skills` 上传 ZIP | — |
| Cursor | `~/.cursor/skills` | `.cursor/skills` |
| Gemini CLI | `~/.gemini/skills` | `.gemini/skills` |
| GitHub Copilot（CLI、编码代理、代码审查、IDE） | `~/.copilot/skills` | `.github/skills` |
| OpenCode | `~/.config/opencode/skills` | `.opencode/skills` |
| Windsurf | `~/.codeium/windsurf/skills` | `.windsurf/skills` |
| Cline | `~/.cline/skills` | `.cline/skills` |
| WorkBuddy | `~/.codebuddy/skills` 或上传 WorkBuddy ZIP | `.codebuddy/skills` |

所有客户端读取 `skills/` 下的同一份源文件，不维护内容不同的平台分叉。目录约定不同的客户端可用 `--agent custom` 指定准确位置。

## 一键安装

需要 Python 3.10+。先克隆仓库：

```bash
git clone https://github.com/songgoldenwind-crypto/ziwei-skills.git
cd ziwei-skills
```

推荐安装方式会同时部署到全部已适配 Agent 的原生用户目录：

```bash
python3 scripts/install.py --agent all --scope user
```

仅安装到开放标准通用目录：

```bash
python3 scripts/install.py
```

只为一个 Agent 安装到项目中：

```bash
python3 scripts/install.py --agent cursor --scope project --target /path/to/project
```

安装到 WorkBuddy 用户目录：

```bash
python3 scripts/install.py --agent workbuddy --scope user
```

适配任意自定义 Agent 目录：

```bash
python3 scripts/install.py --agent custom --destination /path/to/agent/skills
```

已有同名目录时安装器会停止，确认需要替换后加 `--force`。Windows 可把命令中的 `python3` 换成 `py`。

## 各平台分发

### WorkBuddy

从 [最新 Release](https://github.com/songgoldenwind-crypto/ziwei-skills/releases/latest) 下载 `ziwei-skills-workbuddy.zip`，在 WorkBuddy 的“专家·技能·连接器 → 技能 → 添加技能 → 上传技能”中导入。它会显示为“紫微斗数全平台套装”一个卡片，一次安装断盘方法与确定性排盘模块。

`ziwei-workbuddy.zip` 继续保留，供只需要断盘方法的用户单独安装。

WorkBuddy 专用包包含中英文展示说明、版本、作者和工具白名单，并将参考资料转换为 WorkBuddy 的 `@references/...` 引用形式。

### Claude Code 插件市场

在 Claude Code 中执行：

```text
/plugin marketplace add songgoldenwind-crypto/ziwei-skills
/plugin install ziwei-skills@ziwei-skills
```

### Claude 网页、桌面端与 Cowork

从 [最新 Release](https://github.com/songgoldenwind-crypto/ziwei-skills/releases/latest) 下载 `ziwei.zip`，在 `Customize > Skills` 中上传。ZIP 内保留了 Claude 要求的顶层 Skill 文件夹。

### OpenAI 平台

账户中如有 `插件 > Skills > 创建 > 从电脑上传` 入口，可从 [最新 Release](https://github.com/songgoldenwind-crypto/ziwei-skills/releases/latest) 下载 `.skill` 文件并上传。

仓库还包含原生 `.codex-plugin/plugin.json` 和 `.agents/plugins/marketplace.json`。ChatGPT 工作区管理员可在 `管理 > 插件 > 添加 > 导入市场` 中填入仓库 URL，并把路径留空：

```text
https://github.com/songgoldenwind-crypto/ziwei-skills
```

### 通用上传包

生成所有分发文件：

```bash
python3 scripts/package-skills.py
```

`dist/ziwei.skill` 与 `dist/ziwei-agent.zip` 的 `SKILL.md` 位于压缩包根目录；`dist/ziwei.zip` 带顶层 Skill 文件夹，供 Claude 上传；`dist/ziwei-skills-workbuddy.zip` 是 WorkBuddy 单卡完整包；`dist/ziwei-skills-plugin.zip` 同时包含 OpenAI 与 Claude 插件清单。

## 安装排盘模块

排盘模块需要 Python 3.10+：

```bash
cd ziwei-paipan-code
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

安装后可以直接调用：

```bash
python -m ziwei_paipan --date 1990-05-20 --time 12:30 --gender 男 --location 上海
```

完整 CLI 与 JSON 字段说明见 [`ziwei-paipan-code/README.md`](ziwei-paipan-code/README.md)。`geopy` 与 `timezonefinder` 为可选依赖：装上后，内置城市库查不到的地名会走在线地理编码。

## 仓库结构

```text
.
├── .agents/plugins/marketplace.json   # OpenAI 市场适配
├── .claude-plugin/                    # Claude 市场适配
├── .codex-plugin/plugin.json          # OpenAI 插件适配
├── skills/ziwei/
├── ziwei-paipan-code/
├── scripts/
│   ├── install.py
│   ├── package-skills.py
│   ├── test-distribution.py
│   ├── workbuddy_compat.py
│   └── validate-skills.mjs
├── CHANGELOG.md
└── LICENSE
```

## 验证

```bash
node scripts/validate-skills.mjs
python3 scripts/test-distribution.py

cd ziwei-paipan-code
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ziwei_paipan --date 1990-05-20 --time 12:30 --gender 男 --location 上海 --indent 0
```

验证覆盖 Skill 元数据和本地链接、全部 Agent 安装目录、WorkBuddy 元数据及引用转换、覆盖保护、上传包结构。

## 使用许可

本仓库采用 [MIT License](LICENSE)。在保留版权声明和许可声明的前提下，可以使用、复制、修改、合并、发布、分发、再许可和销售软件副本。
