# Claude Code 与 Codex AI 编程插件和 Skills 流程方案

> 调研日期：2026-05-21  
> 目标：为 Claude Code 和 Codex 搭一套可复用、可验证、可扩展的 AI 编程工作流。  
> 结论先行：不要只堆插件。稳定的方案应该是 `AGENTS.md / CLAUDE.md 规则层 + Skills 流程层 + MCP 工具层 + Subagents 并行层 + Hooks/验证层`。

## 1. 核心判断

### 1.1 Claude Code 和 Codex 的插件定位不同

| 维度 | Claude Code | Codex |
| --- | --- | --- |
| 项目常驻规则 | `CLAUDE.md` | `AGENTS.md` |
| 流程复用 | Skills、slash commands | Skills |
| 分发形态 | Plugin 可打包 skills、agents、hooks、MCP、LSP、monitors | Plugin 可打包 skills、app integrations、MCP servers |
| 外部工具 | MCP | MCP、Codex plugins、Connectors |
| 并行分析 | Subagents / agent teams | Subagents |
| 自动化触发 | Hooks | Hooks / commands / non-interactive mode |

落地时建议把两者统一成一种心智模型：

```text
规则文件：告诉 AI 在这个项目里永远遵守什么
Skill：告诉 AI 某类任务该按什么流程做
MCP：给 AI 接入外部工具或实时上下文
Subagent：把可并行的分析、评审、实现任务拆出去
Hook：把必须执行的检查自动化
Plugin：把上述能力打包分发，适合跨项目复用
```

### 1.2 Skills 是最值得优先投资的层

Agent Skills 已经形成开放格式：一个 skill 本质上是包含 `SKILL.md` 的目录，可附带 `scripts/`、`references/`、`assets/` 等资源。它的优势是：

- 可版本控制，适合团队沉淀自己的开发流程。
- 可跨工具复用，Claude Code、Codex、Cursor、Copilot 等生态都在靠近同一类格式。
- 比 MCP 更安全可控，因为很多流程只需要指令和本地脚本，不一定要开放外部服务权限。
- 比超长规则文件更省上下文，只有任务匹配时才加载完整说明。

我的建议：先建 6 个高频 skills，而不是一开始追求几十个插件。

| Skill | 用途 | 优先级 |
| --- | --- | --- |
| `project-analysis` | 新项目架构理解、模块边界、入口文件、风险区识别 | P0 |
| `implementation-plan` | 需求拆解、方案对比、任务清单、验收标准 | P0 |
| `tdd-development` | 测试先行、红绿重构、最小实现 | P0 |
| `code-review` | diff 风险、bug、测试缺口、安全问题 | P0 |
| `frontend-design` | 高质量 UI、设计系统、响应式、可访问性 | P0 |
| `webapp-testing` | 浏览器验证、截图、日志、交互测试 | P0 |
| `mcp-builder` | 给项目自建 MCP Server | P1 |
| `docs-writer` | README、接口文档、变更说明、PR 描述 | P1 |
| `security-review` | 依赖、密钥、权限、注入、越权检查 | P1 |
| `release-checklist` | 提交前检查、版本说明、回滚方案 | P1 |

## 2. 推荐插件和工具清单

### 2.1 Claude Code 必装

| 名称 | 类型 | 用途 | 建议 |
| --- | --- | --- | --- |
| `frontend-design` | Skill | 生成更有设计质量的前端界面 | 已有安装文档，继续保留 |
| `webapp-testing` | Skill | 用 Playwright 类工具验证 Web 应用 | 前端项目必装 |
| `skill-creator` | Skill | 创建、测试、迭代自己的 skills | 做团队流程时必装 |
| `mcp-builder` | Skill | 创建高质量 MCP Server | 有外部系统接入时再装 |
| `Superpowers` | 插件/skills 集 | 需求澄清、计划、TDD、评审、完成分支 | 适合作为开发方法论骨架 |
| `Graphify` | Skill/CLI | 代码图谱、跨模块查询、架构理解 | 本笔记库已经启用 |
| `SuperClaude` | 命令/框架 | 结构化 slash commands、agent、MCP 编排 | 可选，适合重度 Claude Code 用户 |

安装优先级：

```text
第一批：frontend-design、webapp-testing、skill-creator、Graphify
第二批：Superpowers
第三批：mcp-builder、SuperClaude、团队自研 skills
```

说明：SuperClaude 当前稳定版主要是 slash commands 和 MCP 编排，不要把它当成 Claude Code 官方插件。它适合需要大量 `/sc:*` 命令、agent persona、研究/测试/项目管理命令的人；如果只是个人小项目，Superpowers + 自定义 skills 更轻。

### 2.2 Codex 必装或优先配置

| 名称 | 类型 | 用途 | 建议 |
| --- | --- | --- | --- |
| OpenAI Docs MCP | MCP | 查询 OpenAI / Codex / API 官方文档 | 必装 |
| GitHub plugin / GitHub MCP | Plugin/MCP | issue、PR、代码搜索、代码扫描 | 有 GitHub 仓库时装 |
| Figma MCP | MCP | 从 Figma Dev Mode 获取设计上下文 | UI 项目装 |
| Playwright MCP | MCP | 浏览器自动化、前端验证、截图 | 前端项目装 |
| Context7 MCP | MCP | 获取框架和库的实时文档 | 多框架项目装 |
| Graphify skill | Skill/CLI | 知识图谱与跨模块分析 | 本机已装，继续用 |
| 自定义 `code-review` skill | Skill | 固化你的评审标准 | 推荐自己写 |
| 自定义 `frontend-design` skill | Skill | 把 Claude 侧 UI 经验迁移到 Codex | 推荐 |

Codex 的插件和 Skills 区分很清楚：

- 需要连接外部工具、Drive、Gmail、Slack、GitHub 等，用 plugin。
- 需要固定做事流程、团队规范、代码审查清单，用 skill。
- 需要让 Codex 调工具或拿实时上下文，用 MCP。

### 2.3 MCP 选型

| MCP | 用途 | 风险控制 |
| --- | --- | --- |
| OpenAI Docs MCP | OpenAI 官方文档查询 | 只读，风险低 |
| Context7 | 框架/库文档查询 | 只查文档，避免把它当事实唯一来源 |
| GitHub MCP | PR、issue、代码搜索、代码扫描 | 最小权限 token，只启用必要 toolsets |
| Figma MCP | 设计稿上下文、组件变量、Code Connect | 只在需要 UI 还原时启用 |
| Playwright MCP | 浏览器交互、截图、端到端验证 | 只给可信项目使用，谨慎启用任意 JS 执行能力 |
| Serena / 语义代码检索 | 大仓库符号检索、代码理解 | 先在只读模式用 |
| Tavily / Web Search | 深度调研 | 对结果做来源分级，不直接进代码 |

不建议一口气启用很多 MCP。MCP 太多会带来三个问题：工具选择变差、上下文变重、权限边界变复杂。默认只开 `Docs + GitHub + Playwright/Figma 按需`。

## 3. 推荐目录结构

### 3.1 项目内规则

```text
project/
├── AGENTS.md                # Codex 项目规则
├── CLAUDE.md                # Claude Code 项目规则
├── .claude/
│   ├── skills/
│   │   ├── project-analysis/
│   │   ├── implementation-plan/
│   │   ├── code-review/
│   │   └── frontend-design/
│   ├── agents/
│   ├── commands/
│   └── settings.json
├── .codex/
│   ├── agents/
│   └── config.toml          # 仅项目需要时放；项目命令和路径不要写入全局配置
├── .graphify/
└── docs/ai-workflow/
    ├── architecture.md
    ├── testing.md
    ├── release.md
    └── prompts.md
```

### 3.2 全局目录

```text
~/.claude/
├── CLAUDE.md
├── skills/
├── agents/
└── commands/

~/.codex/
├── AGENTS.md
├── skills/
├── agents/
└── config.toml
```

原则：

- 项目强相关规则放项目根目录。
- 个人偏好可以放全局目录，但必须保持短且通用。
- 可跨项目复用的流程沉淀成 skill。
- 要分享给团队时再打包成 plugin。
- 项目命令、目录、业务规则、风险路径、上下文报告只放项目内，避免污染所有项目。
- 全局安装只适合通用 Skills、CLI 和稳定团队流程；详见 `07-全局与项目级边界.md`。

## 4. 一整套 AI 编程流程

### 阶段 0：项目接入

目标：让 AI 先理解项目，不急着写代码。

执行：

```bat
nodesify-graphify run .
nodesify-graphify query "这个项目的主要模块、入口文件、测试方式和风险区域是什么？"
```

产物：

- `.graphify/graph_report.md`
- `docs/ai-workflow/architecture.md`
- 项目根目录 `AGENTS.md` / `CLAUDE.md`

规则文件建议包含：

```markdown
## AI 编程规则

- 修改代码前先说明影响范围和验证计划。
- 跨模块问题优先使用 Graphify。
- 前端改动必须截图验证，必要时使用 Playwright。
- 新增依赖必须说明原因、体积、替代方案。
- 完成任务前必须运行相关测试或说明无法运行的原因。
```

### 阶段 1：需求澄清

使用：

- Claude Code：Superpowers `brainstorming`
- Codex：`implementation-plan` skill

流程：

1. 用户只给目标，不直接让 AI 写代码。
2. AI 输出问题清单、边界、非目标。
3. 确认后生成实现计划。

产物：

```text
需求背景
目标行为
非目标
影响模块
验收标准
风险点
验证命令
```

### 阶段 2：架构与影响分析

使用：

- Graphify
- `project-analysis` skill
- 只读 subagent / explorer

流程：

```bat
nodesify-graphify query "我要修改 X 功能，可能影响哪些模块、接口、测试？"
nodesify-graphify path "模块A" "模块B"
nodesify-graphify explain "核心概念或服务名"
```

适合派 subagent 的任务：

- 一个 agent 查后端影响范围。
- 一个 agent 查前端调用链。
- 一个 agent 查测试覆盖。
- 一个 agent 查安全和权限边界。

不适合派 subagent 的任务：

- 需要马上修改的关键文件。
- 需求还没澄清的开放式实现。
- 会写同一批文件的并行实现。

### 阶段 3：计划和拆分

使用：

- `implementation-plan`
- Superpowers `writing-plans`
- Codex subagents 只用于并行调研，不抢主路径实现

计划模板：

```markdown
## 实现计划

### 改动范围
- 文件/模块

### 步骤
1. 补测试或创建可复现用例
2. 实现最小变更
3. 更新相关文档或类型
4. 运行验证命令
5. 做 diff review

### 验收
- 测试命令
- 手工检查点
- 截图或日志证据
```

### 阶段 4：实现

后端/通用代码：

- 先运行或补测试。
- 小步修改。
- 每完成一个垂直切片就跑验证。
- 避免无关重构。

前端/UI：

- 启用 `frontend-design`。
- 如有设计稿，接 Figma MCP。
- 实现后必须用 Playwright / browser 截图检查。
- 检查响应式、可访问性、文本溢出、交互状态。

建议 prompt：

```text
使用 frontend-design skill。请基于现有设计系统实现这个页面，不要做营销落地页。
完成后启动本地服务，用浏览器检查桌面和移动端截图，修复布局、文本溢出和交互问题。
```

### 阶段 5：验证

使用：

- `webapp-testing`
- Playwright MCP
- 项目 test/lint/build 命令
- Graphify 更新

验证顺序：

```text
静态检查：lint / typecheck
单元测试：unit test
集成测试：integration / e2e
前端截图：desktop + mobile
回归检查：关键流程手工点验
```

前端必须至少输出：

- 本地访问地址。
- 截图检查结果。
- 哪些浏览器/视口验证过。
- 有没有未验证项。

### 阶段 6：代码评审

使用：

- Codex local code review
- Claude/Codex `code-review` skill
- 可并行 subagents：安全、测试、可维护性、性能

评审维度：

| 维度 | 检查点 |
--- | --- |
| Bug | 空值、边界、状态同步、并发、异常路径 |
| 测试 | 是否覆盖新增行为，是否只测实现细节 |
| 安全 | 密钥、权限、注入、越权、外部输入 |
| 性能 | 大列表、重复请求、缓存、渲染 |
| 可维护性 | 命名、边界、重复、复杂度 |
| 产品体验 | 错误状态、加载状态、移动端、可访问性 |

建议 prompt：

```text
请按代码评审模式检查当前 diff，按严重程度列出问题。
只报告真实风险，不要泛泛建议。每个问题给出文件、位置、影响和修复建议。
```

### 阶段 7：提交和复盘

使用：

- `release-checklist`
- Superpowers `finishing-a-development-branch`
- GitHub plugin / MCP

产物：

```markdown
## Summary
- 改了什么

## Verification
- 运行了哪些命令
- 截图/浏览器验证

## Risk
- 风险点
- 回滚方式

## Follow-up
- 后续任务
```

## 5. 安全边界

AI 编程插件的风险主要不在“模型会不会写错”，而在“工具权限被放大”。

必须遵守：

- 第三方 skill / plugin / MCP 装之前先读源码或至少读 manifest。
- MCP 使用最小权限 token。
- 不给不可信 MCP 文件系统、浏览器、shell、邮箱、数据库的组合权限。
- Playwright MCP 的任意 JS 执行能力等同远程代码执行，只给可信客户端启用。
- GitHub MCP 只启用需要的 toolsets，减少工具数量和 token 占用。
- 外部搜索结果不能直接改代码，必须回到官方文档或项目源码验证。
- 密钥、生产数据库、支付、权限系统相关改动必须人工确认。

推荐分级：

| 等级 | 能力 | 是否默认启用 |
| --- | --- | --- |
| L1 | 只读文档 MCP、规则文件、纯文本 skills | 是 |
| L2 | GitHub 只读、Graphify、本地代码检索 | 是 |
| L3 | Playwright、Figma、GitHub 写操作 | 按项目启用 |
| L4 | shell、数据库、邮箱、生产系统 | 默认禁用，任务级授权 |
| L5 | 多工具组合自动化写操作 | 只在隔离环境启用 |

## 6. 建议落地路线

### 第 1 周：打基础

- 整理全局 `~/.codex/AGENTS.md` 和 `~/.claude/CLAUDE.md`。
- 每个项目根目录放简短规则文件。
- 安装/确认 Graphify、frontend-design、webapp-testing、skill-creator。
- Codex 配 OpenAI Docs MCP。

### 第 2 周：形成标准流程

- 写 `project-analysis`、`implementation-plan`、`code-review` 三个自定义 skills。
- 选一个真实项目跑完整流程。
- 把验证命令、测试策略、PR 模板沉淀到项目文档。

### 第 3 周：接入 UI 和外部工具

- 前端项目接 Figma MCP 和 Playwright MCP。
- GitHub 项目接 GitHub plugin/MCP。
- 建立前端截图验证清单。

### 第 4 周：团队化

- 把稳定 skills 打包成 plugin。
- 增加 hooks：提交前 lint/test、禁止误删、检查密钥。
- 建立“AI 生成改动必须有验证记录”的 PR 规范。

## 7. 最小可用配置

如果只想先跑起来，推荐最小集合：

```text
Claude Code:
- frontend-design
- webapp-testing
- skill-creator
- Graphify
- Superpowers

Codex:
- AGENTS.md
- OpenAI Docs MCP
- Graphify skill
- frontend-design skill
- code-review skill

MCP:
- OpenAI Docs MCP
- Context7
- Playwright MCP（前端项目）
- Figma MCP（有设计稿时）
- GitHub MCP（有 PR/issue 流程时）
```

最小流程：

```text
1. Graphify 理解项目
2. implementation-plan 拆需求
3. TDD 或最小变更实现
4. webapp-testing / 项目测试验证
5. code-review 检查 diff
6. release-checklist 输出提交说明
```

## 8. 已有本地文档关系

当前目录已有：

- `frontend-design安装指南.md`：保留，作为 UI skill 单项安装说明。
- `superpowers安装指南.md`：保留，作为 Claude Code 开发方法论安装说明。
- `Graphify安装文档.md`：保留，作为代码图谱安装和日常使用说明。

本文档作为总方案，后续建议再补三份：

- `自定义Skills编写规范.md`
- `AI编程安全边界.md`
- `前端AI开发验证清单.md`

## 9. 参考来源

- Claude Code 插件市场与安装：<https://code.claude.com/docs/en/discover-plugins>
- Claude Code 插件创建：<https://code.claude.com/docs/en/plugins>
- Claude Code 扩展能力总览：<https://code.claude.com/docs/en/features-overview>
- Claude Code subagents：<https://code.claude.com/docs/en/sub-agents>
- Codex CLI：<https://developers.openai.com/codex/cli>
- Codex Plugins：<https://developers.openai.com/codex/plugins>
- Codex Skills：<https://developers.openai.com/codex/skills>
- Codex AGENTS.md：<https://developers.openai.com/codex/guides/agents-md>
- Codex MCP：<https://developers.openai.com/codex/mcp>
- Codex Subagents：<https://developers.openai.com/codex/subagents>
- Agent Skills 开放标准：<https://agentskills.io/>
- OpenAI Skills 仓库：<https://github.com/openai/skills>
- Anthropic Skills 生态索引：<https://www.skills.sh/anthropics/skills>
- Figma MCP：<https://developers.figma.com/docs/figma-mcp-server/>
- Playwright MCP：<https://playwright.dev/docs/getting-started-mcp>
- GitHub MCP：<https://docs.github.com/en/copilot/concepts/context/mcp>
- MCP 官方规范：<https://github.com/modelcontextprotocol/modelcontextprotocol>
- SuperClaude Framework：<https://github.com/SuperClaude-Org/SuperClaude_Framework>
- Awesome Claude Code：<https://github.com/subinium/awesome-claude-code>
