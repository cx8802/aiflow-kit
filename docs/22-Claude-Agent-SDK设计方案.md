# Claude Agent SDK 设计方案

本文描述如何在 `aiflow-kit` 中增加一个基于 Node 的 Claude Agent SDK 能力，用于执行基础、低风险、可自动化的辅助工作，减少 Codex / Claude Code 主会话反复读取大量上下文造成的 token 消耗。

> 说明：用户口头说的 `clause code sdk` 在这里按 Claude Code / Claude Agent SDK 方向设计。实现时以官方当前 SDK 包名和文档为准，不在代码里硬编码版本。

## 当前实现状态

已实现 Phase 1 只读 MVP：

- `aiflow claude-agent install`
- `aiflow claude-agent doctor`
- `aiflow claude-agent run`
- `aiflow claude-agent explore`
- `aiflow claude-agent review-diff`
- `aiflow claude-agent compact`
- `aiflow claude-agent usage`
- Node runner：`node/claude-agent-runner/runner.mjs`
- aiflow-kit 级 SDK 安装目录：`.tools/claude-agent`

默认仍是 disabled，需要配置模型和 API Key 后才真实调用。`--dry-run` 不需要 API Key。

## 目标

- 用 Node 调用 Claude Agent SDK。
- 由 Python 版 `aiflow` CLI 编排，Node runner 只负责 SDK 调用。
- 默认安装到 `aiflow-kit`，不污染全局 npm，也不向目标项目分发 Node SDK 依赖。
- 默认只读，不自动编辑代码。
- API Key、Base URL、模型、代理、预算、工具权限都来自配置。
- 可以配置小模型处理基础任务，必要时再切到更强模型。
- 结果写入 `.aiflow/claude-agent/`，主会话只读取摘要。

## 非目标

- 不把 Claude SDK 做成所有任务的默认执行器。
- 不绕过 Codex / Claude Code 的安全边界。
- 不把数据库密码、API Key、token 写入 `.aiflow/config.toml`、memory 或 docs。
- 不默认开启 `Bash`、`Edit`、`Write`。
- 不执行 `npm install -g`。

## 安装布局

```text
.tools/
└── claude-agent/
    ├── package.json
    ├── package-lock.json
    └── node_modules/

node/
└── claude-agent-runner/
    ├── runner.mjs
    ├── package.json
    └── tasks/
        ├── explore-code.mjs
        ├── summarize-context.mjs
        ├── review-diff.mjs
        ├── compact-context.mjs
        └── diagnose-tests.mjs

.aiflow/
└── claude-agent/
    ├── runs/
    ├── sessions/
    └── usage.jsonl
```

安装命令：

```bat
aiflow claude-agent install
```

内部执行：

```bat
npm install --prefix .tools\claude-agent @anthropic-ai/claude-agent-sdk
```

相对 `package_dir` 始终按 `aiflow-kit` 根目录解析。目标项目只保留 `.aiflow/claude-agent/` 运行结果、上下文和本地 secret；从目标项目调用 `aiflow claude-agent install` 时也复用 `aiflow-kit/.tools/claude-agent`。

是否使用 `npmjs.org`、镜像源或 10808 代理由配置决定。中国网站直连，海外资源按全局 aiflow 代理策略使用 `http://127.0.0.1:10808`。

## 配置设计

`.aiflow/config.toml` 增加：

```toml
[claude_agent]
enabled = false
runtime = "node"

# 不硬编码具体模型。这里配置别名，实际模型名由项目或用户指定。
default_model = "small"
small_model = ""
standard_model = ""
strong_model = ""

# API 配置只放变量名，不放 secret。
api_key_env = "ANTHROPIC_API_KEY"
base_url_env = "ANTHROPIC_BASE_URL"
auth_token_env = ""

# 网络策略。
proxy_mode = "auto"
overseas_proxy = "http://127.0.0.1:10808"
china_direct = true

# 安全和预算。
permission_mode = "dontAsk"
allowed_tools = ["Read", "Glob", "Grep"]
disallowed_tools = ["Bash", "Edit", "Write"]
max_turns = 8
max_budget_usd = 0.20
timeout_seconds = 300

# 输出。
runs_dir = ".aiflow/claude-agent/runs"
sessions_dir = ".aiflow/claude-agent/sessions"
usage_file = ".aiflow/claude-agent/usage.jsonl"
```

`package_dir` 和 runner 路径由 `aiflow-kit` 自己管理，不进入目标项目配置。目标项目配置只声明是否启用、模型/provider、网络、权限、预算和输出位置。

### 模型档位

不在代码里写死模型名，统一走配置：

| 档位 | 用途 |
| --- | --- |
| `small_model` | 摘要、分类、日志归纳、上下文压缩、文档草稿 |
| `standard_model` | 代码结构分析、review、测试失败定位 |
| `strong_model` | 复杂重构方案、跨模块影响分析、高风险任务前置分析 |

运行时命令：

```bat
aiflow claude-agent run "总结 src/aiflow/commands" --model small
aiflow claude-agent review-diff --model standard
aiflow claude-agent explore "分析数据库模块风险" --model strong
```

如果项目没有配置对应模型，命令应该拒绝执行并提示：

```text
claude_agent.small_model is empty. Configure it with:
aiflow config set claude_agent.small_model "<model-name>"
```

## Secret 边界

允许：

```bat
set ANTHROPIC_API_KEY=...
set ANTHROPIC_BASE_URL=...
```

或者项目级本地 secret：

```text
.aiflow/claude-agent.local.toml
.aiflow/secrets.local.toml
```

禁止：

```text
.aiflow/config.toml
.aiflow/memory.md
.aiflow/context.compact.md
docs/
```

`*.local.toml` 已由 gitignore 忽略。

## CLI 命令设计

```bat
aiflow claude-agent install
aiflow claude-agent doctor
aiflow claude-agent run "任务描述"
aiflow claude-agent explore "分析某个目录"
aiflow claude-agent review-diff
aiflow claude-agent compact
aiflow claude-agent diagnose-tests
aiflow claude-agent usage
```

### install

检查：

- Node 是否存在。
- npm 是否存在。
- `aiflow-kit/.tools/claude-agent` 是否可写。
- SDK 包是否安装。
- 是否需要海外代理。

### doctor

检查：

- `claude_agent.enabled`。
- 模型档位是否配置。
- `ANTHROPIC_API_KEY` 或配置的 `api_key_env` 是否存在。
- runner 是否存在。
- Node SDK 是否可 import。
- 权限配置是否安全。

### run

通用入口：

```bat
aiflow claude-agent run "总结当前项目的命令体系" --model small
```

默认：

- 只读。
- 输入 `.aiflow/context.compact.md`。
- 输入 `.aiflow/memory.md`，如果存在。
- 输出到 `.aiflow/claude-agent/runs/<run-id>/result.md`。

### explore

面向代码探索：

```bat
aiflow claude-agent explore "分析 src/aiflow/core/config.py"
```

适合：

- 架构梳理。
- 影响面分析。
- 找命令入口。
- 总结风险。

### review-diff

读取 git diff，生成 review 摘要：

```bat
aiflow claude-agent review-diff
```

输出：

```text
.aiflow/claude-agent/runs/<run-id>/result.md
```

可由 `aiflow review` 引用，但不直接覆盖人工 review。

### compact

用 SDK 进一步压缩上下文：

```bat
aiflow claude-agent compact --model small
```

输入：

```text
.aiflow/context.md
.aiflow/memory.md
.aiflow/plan.md
.aiflow/verify.md
.aiflow/review.md
```

输出：

```text
.aiflow/context.compact.md
```

第一版可以先保留当前 Python 规则压缩作为默认实现；SDK 压缩作为可选增强。

## Node Runner 输入输出

Python CLI 调 Node runner 时传入 JSON 文件，避免命令行参数过长：

```json
{
  "cwd": "<aiflow-kit目录>",
  "task": "explore-code",
  "prompt": "分析 src/aiflow/commands",
  "model": "configured-small-model",
  "allowedTools": ["Read", "Glob", "Grep"],
  "disallowedTools": ["Bash", "Edit", "Write"],
  "permissionMode": "dontAsk",
  "maxTurns": 8,
  "maxBudgetUsd": 0.2,
  "contextFiles": [
    ".aiflow/context.compact.md",
    ".aiflow/memory.md"
  ],
  "outputDir": ".aiflow/claude-agent/runs/20260521-001"
}
```

runner 输出：

```text
.aiflow/claude-agent/runs/<run-id>/
├── input.json
├── result.md
├── messages.jsonl
├── usage.json
└── session.json
```

`usage.json` 至少包含：

```json
{
  "model": "configured-small-model",
  "input_tokens": 0,
  "output_tokens": 0,
  "cache_read_tokens": 0,
  "cache_creation_tokens": 0,
  "total_cost_usd": 0.0
}
```

## 权限策略

默认只允许：

```text
Read
Glob
Grep
```

默认禁止：

```text
Bash
Edit
Write
```

需要编辑时必须显式：

```bat
aiflow claude-agent run "补充 README 小节" --allow-edit
```

即使开启编辑，也建议限制：

```toml
allowed_tools = ["Read", "Glob", "Grep", "Edit"]
disallowed_tools = ["Bash"]
```

涉及安全、数据库、支付、迁移、权限的任务，即使 SDK 生成修改，也必须回到 Codex / Claude Code 主会话人工 review。

## 节省 Token 的方式

核心不是“不消耗 token”，而是减少主会话上下文：

1. 主会话只发一句任务给 `aiflow claude-agent`。
2. SDK 自己读取文件和上下文。
3. SDK 输出短摘要。
4. 主会话只读 `result.md`。
5. 重要结论写入 `.aiflow/memory.md` 或 `.aiflow/context.compact.md`。

这样可以避免在 Codex / Claude Code 主会话里反复塞入大量源码、diff、日志。

## 推荐任务分层

| 任务 | 默认模型 | 权限 |
| --- | --- | --- |
| 上下文压缩 | small | Read/Glob/Grep |
| 日志总结 | small | Read |
| 文档草稿 | small | Read |
| 代码结构分析 | standard | Read/Glob/Grep |
| diff review | standard | Read/Glob/Grep |
| 测试失败诊断 | standard | Read/Glob/Grep |
| 高风险影响分析 | strong | Read/Glob/Grep |
| 自动编辑 | standard/strong | 显式 `--allow-edit` |

## 与 aiflow 现有能力的关系

```text
aiflow context --compact
        ↓
aiflow claude-agent compact
        ↓
.aiflow/context.compact.md

aiflow review
        ↓
aiflow claude-agent review-diff
        ↓
.aiflow/claude-agent/runs/<id>/result.md

aiflow agents plan
        ↓
aiflow claude-agent explore
        ↓
.aiflow/agents/handoff.md
```

## 分阶段实现

### Phase 1：只读 MVP

- `aiflow claude-agent install`
- `aiflow claude-agent doctor`
- `aiflow claude-agent run`
- `aiflow claude-agent usage`
- Node runner 支持 `Read`、`Glob`、`Grep`
- 输出 `result.md` 和 `usage.json`

### Phase 2：上下文压缩与 review

- `aiflow claude-agent compact`
- `aiflow claude-agent review-diff`
- 自动读取 `.aiflow/context.compact.md`
- 将重要结论追加到 `.aiflow/memory.md` 前必须要求确认

### Phase 3：受控编辑

- `--allow-edit`
- 限定可编辑路径。
- 生成 patch 摘要。
- 自动运行 `aiflow verify --auto --continue-on-error`。

### Phase 4：多 Agent 协作

- 与 `.aiflow/agents/tasks/` 对接。
- 每个 SDK run 绑定 task id。
- 输出 handoff。
- 记录 session id，支持 resume。

## 验收标准

- Windows 下只使用 `.bat`、Python、Node，不使用 `.ps1`。
- 不需要全局 npm。
- API Key 不进入 git。
- 小模型、标准模型、强模型都可通过配置切换。
- 默认权限不允许写文件、不允许 Bash。
- 每次调用都有 `result.md`、`usage.json`、退出码。
- 失败时错误信息能说明是配置、网络、认证、模型还是权限问题。
- `aiflow verify --auto` 通过。

## 参考

- Claude Agent SDK overview: <https://code.claude.com/docs/en/agent-sdk/overview>
- Claude Agent SDK quickstart: <https://code.claude.com/docs/en/agent-sdk/quickstart>
- Claude Agent SDK sessions: <https://code.claude.com/docs/en/agent-sdk/sessions>
- Claude Agent SDK permissions: <https://code.claude.com/docs/en/agent-sdk/permissions>
- Claude Agent SDK cost tracking: <https://code.claude.com/docs/en/agent-sdk/cost-tracking>
