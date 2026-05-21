# aiflow-kit 文档索引

`aiflow-kit` 的目标是把 AI 编程中的固定工作流沉淀为可复用的 Skills、插件包装、项目规则模板和轻量 CLI，让 Claude Code 与 Codex 都能稳定走完：

```text
理解项目 -> 拆解计划 -> 编码实现 -> 验证结果 -> 评审交付 -> 复盘沉淀
```

## 建议阅读顺序

| 文档 | 适合场景 |
| --- | --- |
| [Claude Code 与 Codex AI 编程插件和 Skills 流程方案.md](<Claude Code 与 Codex AI 编程插件和 Skills 流程方案.md>) | 调研型总方案，包含插件、MCP、Subagents、Hooks 的完整流程视角 |
| [AI编程全流程工具与Skills项目设计方案.md](AI编程全流程工具与Skills项目设计方案.md) | 原始总体方案和 MVP 范围 |
| [01-开源参考与能力边界.md](01-开源参考与能力边界.md) | 明确哪些能力借鉴开源生态，哪些能力本项目不做 |
| [02-双端适配架构.md](02-双端适配架构.md) | 理解 Claude Code 与 Codex 的目录、规则和插件适配关系 |
| [03-Skills设计规范.md](03-Skills设计规范.md) | 编写核心流程 Skills 和 aiflow 全局辅助 Skills 的格式、触发词、输出契约 |
| [04-CLI与模板安装器规范.md](04-CLI与模板安装器规范.md) | 实现 `aiflow` CLI、配置文件、模板生成和验证命令 |
| [05-插件分发与安装流程.md](05-插件分发与安装流程.md) | 设计 Claude Code 插件、Codex 插件、本地安装和 marketplace |
| [06-MVP实施路线与验收清单.md](06-MVP实施路线与验收清单.md) | 拆分第一版开发任务和可验收标准 |
| [07-全局与项目级边界.md](07-全局与项目级边界.md) | 明确哪些能力可以全局安装，哪些必须留在项目内，避免污染所有项目 |
| [08-项目级多语言环境配置.md](08-项目级多语言环境配置.md) | 配置 Go、Node、Java、Maven、Python 的项目级隔离环境 |
| [09-MVP实现落地方案.md](09-MVP实现落地方案.md) | 从文档方案落到可运行 Python CLI、模板和内置 Skills |
| [10-运行时与脚本语言边界.md](10-运行时与脚本语言边界.md) | 说明哪些能力用 Python，哪些能力交给 Go、Node、Java、BAT 或 ripgrep |
| [11-使用方式与安装策略.md](11-使用方式与安装策略.md) | 说明源码版、安装版、目标项目安装、环境变量和全局安装策略 |
| [12-Codex与Claude全局接入.md](12-Codex与Claude全局接入.md) | 说明如何让 Codex 和 Claude Code 在全局知道 aiflow |
| [13-快速安装.md](13-快速安装.md) | 一键安装 Codex 用户级 Skills，并生成 Claude/Codex 插件包 |
| [14-测试与质量检查.md](14-测试与质量检查.md) | 说明 unittest、compileall 和 CLI smoke test 的运行方式 |
| [15-数据库连接项目级配置.md](15-数据库连接项目级配置.md) | 说明如何把数据库连接保存为项目级配置并保护 secret |
| [16-在其他项目中安装aiflow-kit.md](16-在其他项目中安装aiflow-kit.md) | 说明 Codex/Claude 如何用 `D:\code_work\aiflow-kit` 源码路径给其他项目安装 aiflow-kit |
| [17-多Agent协作流程.md](17-多Agent协作流程.md) | 说明多 Agent 角色、任务队列、项目级 handoff 和全局 Skills 边界 |
| [18-安装路径与环境探测.md](18-安装路径与环境探测.md) | 说明如何自动探测本机 aiflow-kit 路径、生成 `.aiflow/env.local.toml` 并渲染全局 Skills |

## 辅助安装文档

这些文档保留为外部能力的单项安装参考，不作为 MVP 的强依赖：

| 文档 | 用途 |
| --- | --- |
| [Graphify安装文档.md](other/Graphify安装文档.md) | 代码图谱工具安装和项目初始化 |
| [frontend-design安装指南.md](other/frontend-design安装指南.md) | 前端设计类 Skill 安装和使用 |
| [superpowers安装指南.md](other/superpowers安装指南.md) | Superpowers 方法论和 Skills 安装 |

## 第一版交付物

第一版只交付可落地的工程骨架，不做大型平台：

- 5 个核心流程 Skills：`project-analysis`、`implementation-plan`、`tdd-development`、`frontend-verify`、`code-review-release`，3 个全局辅助 Skills：`aiflow-kit-guide`、`aiflow-kit-installer`、`aiflow-kit-updater`，以及 4 个多 Agent Skills：`multi-agent-orchestrator`、`multi-agent-explorer`、`multi-agent-worker`、`multi-agent-reviewer`。
- 一个轻量 CLI：`aiflow init/context/plan/review/verify/doctor/install-skills`。
- Claude Code 插件包：`.claude-plugin/plugin.json` + `skills/`。
- Codex 插件包：`.codex-plugin/plugin.json` + `skills/`。
- 项目规则模板：`AGENTS.md`、`CLAUDE.md`、`.aiflow/config.toml`。

## 关键原则

- Skills 只放流程和判断标准，确定性扫描交给 CLI。
- `AGENTS.md` 和 `CLAUDE.md` 保持短，只做项目级约束和入口指针。
- 插件是分发单元，Skills 是工作流单元，CLI 是确定性工具单元。
- 全局只放通用流程，项目事实只放项目目录，默认不污染用户全局配置。
- 文件扫描优先使用系统 `ripgrep`，不可用时回退到 Python 遍历。
- Python 做 CLI 主控，BAT 做 Windows 环境激活，Node/Go/Java 只调用各自生态工具。
- 第一版不默认接入 MCP、不自动提交、不自动发 PR、不替代测试框架。

## 参考来源

截至 2026-05-21，本文档集参考了这些公开文档和开源项目：

- Agent Skills 标准：https://agentskills.io/
- Anthropic Agent Skills 示例库：https://github.com/anthropics/skills
- Claude Code 插件文档：https://code.claude.com/docs/en/plugins
- Claude Code 插件参考：https://code.claude.com/docs/en/plugins-reference
- OpenAI Codex Skills 文档：https://developers.openai.com/codex/skills
- OpenAI Codex Plugins 文档：https://developers.openai.com/codex/plugins
- Superpowers 开源工作流：https://github.com/obra/superpowers
