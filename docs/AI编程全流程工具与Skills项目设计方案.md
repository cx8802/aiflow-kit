# AI 编程全流程工具与 Skills 项目设计方案

> 基于：`Claude Code 与 Codex AI 编程插件和 Skills 流程方案.md`  
> 目标：自建一套轻量、可复用、同时服务 Claude Code 和 Codex 的 AI 编程流程工具。  
> 原则：只做“流程标准化 + 项目上下文 + 验证闭环”，不做大而全的平台。

## 1. 项目定位

项目暂定名：`aiflow-kit`

一句话定位：

```text
把需求分析、项目理解、实现计划、编码验证、代码评审、交付复盘这条 AI 编程流程，沉淀成可安装的 skills、规则模板和轻量 CLI。
```

它不是：

- 不是新的 AI 聊天工具。
- 不是新的代码生成器。
- 不是 Claude Code / Codex 的替代品。
- 不是完整 MCP 平台。
- 不是项目管理系统。

它要解决的问题：

- 每次让 AI 写代码都容易直接开干，缺少固定流程。
- Claude Code 和 Codex 的规则、skills、验证方式分散。
- 项目上下文、测试命令、评审标准没有统一沉淀。
- 前端改动缺少截图验证闭环。
- 提交前缺少结构化 review 和 release checklist。

## 2. MVP 范围

第一版只做 3 件事：

```text
1. 提供 5 个核心 skills
2. 提供 1 个轻量 CLI：aiflow
3. 提供 Claude Code / Codex 项目模板安装器
```

### 2.1 核心 Skills

| Skill | 触发场景 | 核心产物 |
| --- | --- | --- |
| `project-analysis` | 接手新项目、改动前理解项目 | 架构摘要、模块边界、风险区、验证命令 |
| `implementation-plan` | 开发前拆需求 | 实现步骤、影响范围、验收标准 |
| `tdd-development` | 编码实现 | 测试先行流程、最小变更策略 |
| `frontend-verify` | 前端/UI 改动 | 设计检查、浏览器验证、截图要求 |
| `code-review-release` | 完成后自检 | diff review、测试结果、PR/提交说明 |

这 5 个 skills 对应完整链路：

```text
理解项目 -> 拆需求 -> 写代码 -> 验证 UI/测试 -> 评审交付
```

### 2.2 轻量 CLI

CLI 名称：`aiflow`

第一版只做确定性辅助，不接 LLM，不自动改代码。

| 命令 | 作用 |
| --- | --- |
| `aiflow init` | 在当前项目生成 `AGENTS.md`、`CLAUDE.md`、`.aiflow/config.toml` |
| `aiflow doctor` | 检查 Git、Node、Python、Graphify、测试命令、skills 是否可用 |
| `aiflow context` | 汇总项目结构、技术栈、入口、测试命令，生成 `.aiflow/context.md` |
| `aiflow plan` | 生成实现计划模板 |
| `aiflow review` | 汇总 git diff、变更文件、风险提示，生成 review 模板 |
| `aiflow verify` | 按配置运行 lint/test/build 或输出应运行命令 |
| `aiflow install-skills` | 默认安装 skills 到当前项目；全局安装必须显式确认 |

### 2.3 不做的内容

第一版明确不做：

- 不做 Web UI。
- 不做 MCP Server。
- 不做复杂 agent 调度平台。
- 不做跨仓库知识库。
- 不做自动提交、自动发 PR。
- 不做自己的代码图谱，优先调用 Graphify。
- 不做完整测试框架，只发现和执行项目已有命令。

## 3. 总体架构

```text
Claude Code / Codex
        |
        | 读取 skills 和规则文件
        v
项目规则层
AGENTS.md / CLAUDE.md
        |
        | 调用
        v
aiflow CLI
        |
        | 读取项目与 Git 信息
        v
.aiflow/
context.md
plan.md
review.md
verify.md
config.toml
        |
        | 可选调用
        v
Graphify / 测试命令 / Playwright / Figma / GitHub
```

分层职责：

| 层 | 职责 |
| --- | --- |
| Skills | 告诉 Claude Code / Codex 遇到某类任务时该怎么做 |
| 规则文件 | 固定项目级约束，比如先分析、后实现、必须验证 |
| CLI | 做确定性扫描、模板生成、命令检查、报告汇总 |
| Graphify | 做跨模块架构查询和代码关系分析 |
| 外部 MCP | 只在需要时接 Figma、Playwright、GitHub、Docs |

## 4. 推荐项目结构

```text
aiflow-kit/
├── README.md
├── pyproject.toml
├── src/
│   └── aiflow/
│       ├── __init__.py
│       ├── cli.py
│       ├── commands/
│       │   ├── init.py
│       │   ├── doctor.py
│       │   ├── context.py
│       │   ├── plan.py
│       │   ├── review.py
│       │   ├── verify.py
│       │   └── install_skills.py
│       ├── core/
│       │   ├── project_scan.py
│       │   ├── git_diff.py
│       │   ├── command_detect.py
│       │   ├── risk_rules.py
│       │   └── report.py
│       └── templates/
│           ├── AGENTS.md
│           ├── CLAUDE.md
│           ├── config.toml
│           ├── plan.md
│           ├── review.md
│           └── verify.md
├── skills/
│   ├── project-analysis/
│   │   └── SKILL.md
│   ├── implementation-plan/
│   │   └── SKILL.md
│   ├── tdd-development/
│   │   └── SKILL.md
│   ├── frontend-verify/
│   │   └── SKILL.md
│   └── code-review-release/
│       └── SKILL.md
├── examples/
│   ├── AGENTS.md
│   ├── CLAUDE.md
│   └── aiflow.config.toml
└── tests/
```

语言建议：

- CLI 用 Python，便于 Windows 环境和文本处理。
- 不引入重框架。
- CLI 只依赖标准库 + 少量成熟库。
- 输出以 Markdown 为主，JSON 作为后续扩展。

## 5. 配置设计

项目生成 `.aiflow/config.toml`：

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

[graphify]
enabled = true
read_report_before_search = true

[frontend]
enabled = false
dev_url = "http://localhost:3000"
desktop_viewport = "1440x900"
mobile_viewport = "390x844"

[review]
high_risk_paths = [
  "auth/",
  "security/",
  "payment/",
  "database/",
  "migrations/"
]
require_tests = true
require_verification_summary = true

[skills]
install_to_codex_repo = true
install_to_codex_user = false
install_to_claude_plugin = true
allow_global_install = false
```

`aiflow doctor` 负责检查配置缺失项，不自动猜错关键命令。

全局和项目级边界：

- 可以全局：`aiflow` CLI、通用 Skills、稳定团队流程。
- 必须项目级：`AGENTS.md`、`CLAUDE.md`、`.aiflow/config.toml`、`.aiflow/context.md`、项目命令、风险路径、业务规则、项目定制 Skills。
- 默认不写用户全局目录，避免一个项目的规则污染所有项目。详细规则见 `07-全局与项目级边界.md`。

## 6. Skills 设计

### 6.1 project-analysis

触发场景：

- “帮我理解这个项目”
- “我要改某个功能，先分析影响范围”
- “这个模块和那个模块有什么关系”

流程：

```text
1. 先读取项目规则
2. 如存在 .graphify，先读 graph_report.md
3. 跨模块问题用 nodesify-graphify query/path/explain
4. 调用 aiflow context 生成项目摘要
5. 输出入口、模块、风险区、建议阅读文件、验证命令
```

### 6.2 implementation-plan

触发场景：

- “实现某功能”
- “修某 bug”
- “加一个页面/接口”

流程：

```text
1. 复述目标和非目标
2. 识别影响范围
3. 生成 3-7 步实现计划
4. 明确测试和验收标准
5. 对高风险项要求用户确认
```

### 6.3 tdd-development

触发场景：

- “按测试驱动做”
- “补测试”
- “修这个失败测试”

流程：

```text
1. 找到已有测试风格
2. 先写或调整最小失败测试
3. 实现最小通过代码
4. 重构
5. 运行相关测试
```

### 6.4 frontend-verify

触发场景：

- UI 页面
- 组件
- 样式
- 交互
- 响应式

流程：

```text
1. 识别设计系统和现有组件
2. 实现 UI，不做无关营销页
3. 启动 dev server
4. 桌面和移动端截图验证
5. 检查文本溢出、交互状态、空状态、加载状态
6. 输出验证结果
```

### 6.5 code-review-release

触发场景：

- “检查当前 diff”
- “提交前 review”
- “写 PR 描述”

流程：

```text
1. 调用 aiflow review 汇总 diff
2. 按严重程度检查 bug、测试、安全、性能、维护性
3. 调用 aiflow verify 或列出验证命令
4. 输出 Summary / Verification / Risk / Follow-up
```

## 7. CLI 输出契约

### 7.1 `aiflow context`

输出 `.aiflow/context.md`：

```markdown
# Project Context

## Tech Stack

## Entrypoints

## Important Directories

## Test Commands

## Risk Areas

## Graphify
```

### 7.2 `aiflow plan`

输出 `.aiflow/plan.md`：

```markdown
# Implementation Plan

## Goal

## Non-goals

## Impact Scope

## Steps

## Verification

## Risks
```

### 7.3 `aiflow review`

输出 `.aiflow/review.md`：

```markdown
# Review Input

## Changed Files

## Diff Summary

## High Risk Signals

## Missing Verification

## Suggested Checks
```

## 8. 安装和使用体验

### 8.1 安装

```bat
pipx install aiflow-kit
```

或开发阶段：

```bat
git clone <repo>
cd aiflow-kit
pip install -e .
```

### 8.2 初始化项目

```bat
aiflow init
aiflow doctor
aiflow install-skills
```

初始化后生成：

```text
AGENTS.md
CLAUDE.md
.aiflow/config.toml
.aiflow/context.md
```

### 8.3 日常使用

```text
用户：帮我实现这个功能，先按项目流程分析和计划。

AI：
1. 读取 AGENTS.md / CLAUDE.md
2. 触发 project-analysis
3. 调用 aiflow context
4. 如需跨模块分析，调用 Graphify
5. 触发 implementation-plan
6. 用户确认后开始实现
7. 完成后触发 code-review-release
```

## 9. 与现有插件的关系

| 已有能力 | 本项目怎么用 |
| --- | --- |
| Graphify | 不重复造图谱，只调用它做架构和跨模块查询 |
| frontend-design | 可以直接复用，也可以把规则吸收到 `frontend-verify` |
| Superpowers | 借鉴 brainstorming / TDD / review 流程，不强依赖 |
| Playwright MCP | 前端验证阶段按需接入 |
| Figma MCP | 有设计稿时按需接入 |
| GitHub MCP | 第二阶段再接 PR/issue 自动化 |

第一版保持独立：没有这些 MCP 也能跑，只是能力弱一些。

## 10. 开发路线

### 阶段 1：文档和模板

目标：先能安装规则和 skills。

任务：

- 写 5 个 `SKILL.md`。
- 写 `AGENTS.md` / `CLAUDE.md` 模板。
- 写 `.aiflow/config.toml` 模板。
- 写 README。

验收：

```text
aiflow init 能生成项目规则文件和配置文件
aiflow install-skills 能复制 skills 到 Claude Code / Codex 目录
```

### 阶段 2：CLI MVP

目标：让 AI 可以调用确定性工具拿上下文。

任务：

- 实现 `doctor`
- 实现 `context`
- 实现 `plan`
- 实现 `review`
- 实现 `verify`

验收：

```text
aiflow doctor 能发现缺失命令
aiflow context 能生成项目摘要
aiflow review 能识别 changed files 和高风险路径
aiflow verify 能运行配置中的验证命令
```

### 阶段 3：真实项目试跑

目标：用一个前端项目和一个后端项目验证流程。

任务：

- 在真实项目跑完整链路。
- 修正 skills 触发词和输出格式。
- 补充 Windows `cmd` / `.bat` 兼容问题，避免依赖 PowerShell `.ps1`。
- 明确哪些检查必须人工确认。

验收：

```text
完成一次功能开发，从分析到提交说明都有结构化产物
前端项目能产出截图验证记录
后端项目能产出测试和 review 记录
```

### 阶段 4：可选增强

只在 MVP 稳定后做：

- JSON 输出。
- GitHub PR 描述生成。
- Playwright 命令自动发现。
- MCP Server 包装。
- 团队 plugin 打包。

## 11. 风险控制

| 风险 | 控制 |
| --- | --- |
| 项目变得太大 | MVP 只做 5 skills + 1 CLI |
| 规则太长，AI 不读 | skills 分场景加载，规则文件保持短 |
| CLI 自动化误操作 | 第一版不自动改代码、不自动提交 |
| 验证命令误判 | `doctor` 只提示，关键命令让用户配置 |
| MCP 权限过大 | 第一版不内置 MCP，只写按需接入说明 |
| 与 Graphify 重复 | 只调用 Graphify，不自己做图谱 |

## 12. 第一版完成标准

第一版算完成，需要满足：

- 可以在任意项目运行 `aiflow init`。
- Claude Code 和 Codex 都能读取对应规则。
- 5 个 skills 都有明确触发场景、流程、输出要求。
- `aiflow context/review/verify` 能稳定生成 Markdown。
- 前端改动有 `frontend-verify` 流程。
- 提交前有 `code-review-release` 流程。
- 不依赖复杂服务，不需要数据库，不需要 Web UI。

最终目标不是“功能多”，而是让 AI 编程每次都能稳定走完：

```text
分析 -> 计划 -> 实现 -> 验证 -> 评审 -> 交付
```
