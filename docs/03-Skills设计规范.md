# Skills 设计规范

本项目的 Skills 采用 Agent Skills 风格：一个目录，一个 `SKILL.md`，必要时附带 `scripts/`、`references/`、`assets/`。第一版优先做 instruction-only Skills，只有确定性、重复性很强的逻辑才下沉到 CLI。

## Skill 目录格式

```text
skills/<skill-name>/
├── SKILL.md
├── references/   # 可选，长文档或样例
├── scripts/      # 可选，确定性脚本
└── assets/       # 可选，模板资源
```

## SKILL.md 基础模板

```markdown
---
name: project-analysis
description: Use when an AI coding task needs repository understanding, impact analysis, architecture mapping, risk discovery, or verification command discovery before implementation.
---

# Project Analysis

## Workflow

1. Read project rules from AGENTS.md and CLAUDE.md when present.
2. Run or request `aiflow context` if `.aiflow/context.md` is missing or stale.
3. Inspect only the files needed to answer the current task.
4. Summarize architecture, affected modules, risks, and verification commands.

## Output

- Goal
- Relevant modules
- Files to inspect
- Risk areas
- Verification commands
```

## 写作规则

- `description` 必须包含触发场景和边界，因为 agent 会先根据它判断是否加载 Skill。
- 每个 Skill 只做一件事，避免把“分析、计划、实现、review”写进同一个 Skill。
- 正文使用命令式步骤，写清输入和输出。
- 长背景放到 `references/`，`SKILL.md` 只放关键流程。
- 脚本只用于确定性任务，例如解析 `package.json`、读取 Git diff、生成报告。
- 不在 Skill 内假设一定有 MCP、GitHub、浏览器或 Figma。

## 五个核心 Skills

### project-analysis

触发场景：

- 新接手项目。
- 修改前需要理解架构和影响范围。
- 用户要求“先分析”“先看项目”“找相关文件”。
- 需要发现测试、构建、启动命令。

流程：

```text
1. 读取 AGENTS.md / CLAUDE.md / .aiflow/config.toml。
2. 如果 .aiflow/context.md 不存在，调用 aiflow context。
3. 如果存在 Graphify 或类似代码图谱报告，先读取报告摘要。
4. 搜索相关入口、模块、测试和配置。
5. 输出影响范围、风险点、建议阅读文件、验证命令。
```

输出：

```markdown
## Project Analysis

### Goal

### Relevant Modules

### Important Files

### Risk Areas

### Verification

### Open Questions
```

### implementation-plan

触发场景：

- 用户要求实现功能、修 bug、重构、加接口、加页面。
- `project-analysis` 后需要形成可执行计划。
- 涉及多文件、多步骤或有风险边界。

流程：

```text
1. 复述目标和非目标。
2. 列出影响范围。
3. 拆成 3-7 个步骤。
4. 每步写清文件范围和验证方式。
5. 对高风险项列出需确认的问题。
```

输出：

```markdown
## Implementation Plan

### Goal

### Non-goals

### Impact Scope

### Steps

### Verification

### Risks
```

### tdd-development

触发场景：

- 用户明确要求 TDD。
- 修复现有失败测试。
- 需求涉及核心逻辑、数据处理、权限、计费、安全等高风险代码。

流程：

```text
1. 找已有测试位置、命名和断言风格。
2. 先补最小失败测试或复现用例。
3. 实现最小通过代码。
4. 重构并保持行为不变。
5. 运行相关测试，记录结果。
```

输出：

```markdown
## TDD Result

### Test Added or Updated

### Implementation

### Verification

### Remaining Risk
```

### frontend-verify

触发场景：

- 前端页面、组件、样式、交互、响应式布局。
- 用户提供截图、设计稿、Figma 或 UI 反馈。
- 改动可能影响视觉、可用性或布局。

流程：

```text
1. 识别技术栈、设计系统、组件库和现有页面风格。
2. 实现前端改动。
3. 启动或提示 dev server。
4. 验证桌面和移动视口。
5. 检查布局溢出、空状态、加载状态、错误状态和关键交互。
6. 输出截图路径或无法截图原因。
```

输出：

```markdown
## Frontend Verification

### Viewports

### Checked Flows

### Screenshots

### Issues Found

### Verification Commands
```

### code-review-release

触发场景：

- 用户要求 review、提交前检查、写 PR 描述、总结改动。
- 完成实现后需要自检。
- 存在 Git diff。

流程：

```text
1. 调用 aiflow review 汇总 changed files 和风险信号。
2. 按严重程度检查 bug、测试缺口、安全、性能、兼容性。
3. 调用 aiflow verify 或列出应运行命令。
4. 输出 review 结论、验证结果、风险和 PR 摘要。
```

输出：

```markdown
## Review

### Findings

### Verification

### Risk

### PR Summary

### Follow-up
```

## Skill 触发链路

推荐默认链路：

```text
project-analysis
  -> implementation-plan
  -> tdd-development 或普通实现
  -> frontend-verify 或 aiflow verify
  -> code-review-release
```

用户要求很简单时，可以跳过显式计划，但高风险改动不跳过分析和验证。

## 触发测试清单

每个 Skill 合入前至少用这些 prompt 做匹配测试：

- “先帮我理解这个项目结构。”
- “实现登录页的手机号验证码流程，先给计划。”
- “按 TDD 修这个 parser bug。”
- “这个按钮在移动端错位了，帮我修并截图验证。”
- “检查当前 diff，给我 PR 描述。”

如果 agent 经常误触发，先收窄 `description`，不要在正文里补救。
