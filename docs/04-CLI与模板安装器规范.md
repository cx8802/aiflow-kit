# CLI 与模板安装器规范

`aiflow` CLI 是本项目的确定性执行层。它不调用 LLM，不直接做业务代码修改，只负责扫描、生成报告、复制模板、执行用户配置的验证命令。

## CLI 命令总览

| 命令 | 作用 | 输出 |
| --- | --- | --- |
| `aiflow init` | 初始化项目规则和配置 | `AGENTS.md`、`CLAUDE.md`、`.aiflow/config.toml` |
| `aiflow doctor` | 检查环境和配置 | 控制台报告，可选 `.aiflow/doctor.md` |
| `aiflow context` | 汇总项目上下文 | `.aiflow/context.md` |
| `aiflow plan` | 生成计划模板 | `.aiflow/plan.md` |
| `aiflow review` | 汇总 diff 和风险 | `.aiflow/review.md` |
| `aiflow verify` | 执行或列出验证命令 | `.aiflow/verify.md` |
| `aiflow install-skills` | 安装 Skills 到目标位置 | 复制结果和冲突报告 |
| `aiflow browser` | 浏览器平台打包、adapter capture bridge 和本地 capture | `.aiflow/browser/` |

## 配置文件

`.aiflow/config.toml`：

```toml
[project]
name = "your-project"
type = "auto"

[commands]
install = ""
lint = ""
typecheck = ""
test = ""
build = ""
dev = ""

[context]
include = [
  "README.md",
  "package.json",
  "pyproject.toml",
  "src",
  "app",
  "tests"
]
exclude = [
  ".git",
  "node_modules",
  "dist",
  "build",
  ".next",
  ".venv"
]

[frontend]
enabled = false
dev_url = "http://localhost:3000"
desktop_viewport = "1440x900"
mobile_viewport = "390x844"

[browser]
enabled = false
host = "127.0.0.1"
port = 8765
capture_dir = ".aiflow/browser/captures"
elements_dir = ".aiflow/browser/elements"
actions_dir = ".aiflow/browser/actions"
token_file = ".aiflow/browser/token"
max_payload_bytes = 200000

[review]
require_tests = true
require_verification_summary = true
high_risk_paths = [
  "auth/",
  "security/",
  "payment/",
  "database/",
  "migrations/"
]

[skills]
install_to_codex_repo = true
install_to_codex_user = false
install_to_claude_user = false
install_to_claude_plugin = true
allow_global_install = false
```

## `aiflow init`

职责：

- 创建 `.aiflow/`。
- 生成 `.aiflow/config.toml`。
- 生成或提示合并 `AGENTS.md`。
- 生成或提示合并 `CLAUDE.md`。
- 不覆盖已有文件，默认写 `.new` 或提示 `--force`。
- 只写当前项目，不修改用户全局 `AGENTS.md`、`CLAUDE.md`、Codex/Claude 配置或全局 skills 目录。

建议参数：

```bat
aiflow init
aiflow init --force
aiflow init --no-claude
aiflow init --no-codex
```

## `aiflow context`

扫描输入：

- Git 根目录。
- 文件清单优先使用 `rg --files`，没有 ripgrep 时回退到 Python 遍历。
- 常见包管理文件：`package.json`、`pnpm-lock.yaml`、`pyproject.toml`、`requirements.txt`、`go.mod`、`Cargo.toml`。
- README 和 docs 索引。
- 源码目录和测试目录。
- 配置中的 include/exclude。

输出：

```markdown
# Project Context

## Generated At

## Tech Stack

## Entrypoints

## Important Directories

## Test Commands

## Build Commands

## Risk Areas

## Notes for AI Agents
```

## `aiflow review`

扫描输入：

- `git status --short`
- `git diff --stat`
- `git diff --name-only`
- 配置中的 high risk paths
- 是否有测试文件变更

输出：

```markdown
# Review Input

## Changed Files

## Diff Summary

## High Risk Signals

## Test Coverage Signals

## Missing Verification

## Suggested Checks
```

风险识别第一版只做规则匹配：

- 命中高风险路径。
- 修改 lockfile。
- 修改迁移脚本。
- 修改认证、权限、支付、安全关键词文件。
- 有生产代码变更但无测试变更。
- 删除大量文件。

## `aiflow verify`

执行顺序：

```text
lint -> typecheck -> test -> build
```

规则：

- 只运行 `.aiflow/config.toml` 中显式配置的命令。
- 未配置时只输出建议，不猜测执行。
- 每条命令记录开始时间、结束时间、退出码。
- 失败后默认停止，支持 `--continue-on-error`。

输出：

```markdown
# Verification

## Commands

## Results

## Failed Command

## Notes
```

## `aiflow install-skills`

安装目标：

| 参数 | 目标 |
| --- | --- |
| `--target codex-repo` | 当前项目 `.agents/skills/` |
| `--target codex-user` | `$HOME/.agents/skills/` |
| `--target claude-user` | `$HOME/.claude/skills/` |
| `--target claude-plugin` | 生成 Claude Code 插件目录 |
| `--target codex-plugin` | 生成 Codex 插件目录 |
| `--target all` | 按配置安装 |

默认策略：

- 不传 `--target` 时等价于 `--target codex-repo`，只影响当前项目。
- `codex-user`、`claude-user`、用户级 marketplace 都属于全局安装，必须要求 `--confirm-global` 和 `--allow-global`。
- 配置中的 `allow_global_install = false` 时，拒绝用户级安装。
- 全局安装前输出污染风险提示，提醒只安装通用 Skills。

冲突策略：

- 目标不存在则创建。
- 目标存在且内容相同则跳过。
- 目标存在且内容不同则写入 `.bak` 或要求 `--force`。
- 输出复制清单。

全局污染检查：

- 如果 Skill 或模板中包含具体项目名、绝对路径、业务域名、测试命令、构建命令、secret 字样，应拒绝用户级安装。
- 如果目标是项目 `.agents/skills/`，允许包含项目特定说明。
- 安装报告中必须标明 scope：`project`、`user` 或 `team`。

## 模板生成规则

`AGENTS.md` 和 `CLAUDE.md` 只生成最小规则：

```markdown
# AI Agent Instructions

## Project Workflow

- Before non-trivial changes, run or read `.aiflow/context.md`.
- For implementation work, create or update `.aiflow/plan.md`.
- Before final response or commit, run configured verification or explain why it was not run.

## Commands

- Context: `aiflow context`
- Review: `aiflow review`
- Verify: `aiflow verify`
```

## 实现建议

- CLI 使用 Python 标准库优先。
- 文件扫描优先使用系统已安装的 `ripgrep`，命令为 `rg --files --hidden --glob !.git/**`；不可用时回退到 Python。
- TOML 读取在 Python 3.11+ 用 `tomllib`，写入模板用静态文件。
- 命令执行使用 `subprocess.run`，不要 shell 拼接用户输入。
- 文件扫描使用白名单入口和 exclude 目录，避免扫入 `node_modules`、`.git`、构建产物。
- Markdown 输出保持稳定，便于 Skills 引用固定标题。
