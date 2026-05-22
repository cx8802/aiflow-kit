# aiflow-kit

为 Codex、Claude Code 和多 Agent 协作提供项目上下文、Skills、验证评审与 Gitee/GitHub 自动化的 AI 编程工作流工具包。

`aiflow-kit` 用一个轻量 Python CLI、一组项目模板和一套可复用 Skills，把 AI 编程里最容易失控的环节固定下来：项目理解、任务计划、编码实现、验证评审、发版自动化和项目记忆沉淀。它不是 Apache Airflow，也不是新的 IDE；它更像是给 AI 编程代理使用的项目级“工作流脚手架”。

```text
理解项目 -> 制定计划 -> 编码实现 -> 验证结果 -> 评审交付 -> 发布复盘
```

## 项目简介

适合放到 Gitee 仓库侧边栏的简介：

```text
AI 编程工作流工具包：为 Codex/Claude Code 提供项目上下文、Skills、验证评审、多 Agent 协作与 Gitee/GitHub 自动化。
```

推荐标签：

```text
AI编程, Codex, Claude Code, Skills, CLI, 多Agent, 自动化, Python
```

## 解决什么问题

AI 编程真正麻烦的地方，通常不是“让模型写一段代码”，而是让它持续、稳定、可审计地完成一次工程任务：

- 不重复解释项目背景。
- 不把项目事实写进用户全局配置。
- 不跳过计划、测试和评审。
- 不把密钥、数据库连接、远程 token 混进仓库。
- 不让多个 Agent 互相覆盖现场。
- 不让发版停在“推了 tag，但 Release 页面还是空”的半路。

`aiflow-kit` 把这些约束放进项目内的 `.aiflow/`、`AGENTS.md`、`CLAUDE.md` 和 `.agents/skills/`，让 Codex 和 Claude Code 在同一个仓库里按同一套规则工作。

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 项目初始化 | 生成 `AGENTS.md`、`CLAUDE.md`、`.aiflow/config.toml`，建立项目级 AI 工作规则 |
| 上下文压缩 | 生成 `.aiflow/context.md` 和 `.aiflow/context.compact.md`，减少重复读仓库的成本 |
| 项目记忆 | 用 `aiflow memory` 保存可复用项目事实，默认留在当前仓库 |
| Skills 分发 | 内置分析、计划、TDD、前端验证、发布评审、多 Agent、Gitee/GitHub 等 Skills |
| 验证与评审 | 用 `aiflow verify`、`aiflow review` 固化测试、构建和交付前检查 |
| 多 Agent 协作 | 用 `.aiflow/agents/` 维护任务队列、角色分工、handoff 和状态 |
| 代码托管自动化 | 用 `aiflow forge` 自动识别 Gitee/GitHub 仓库并创建/查询 Release |
| 伴随工具 | 支持浏览器上下文采集、数据库 profile、Nacos、WSL、SSH、Claude Agent SDK worker |

## 快速开始

源码方式运行：

```bat
cd /d D:\code_work\aiflow-kit
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python -m aiflow --help
```

Windows 下推荐使用仓库脚本：

```bat
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat --help
```

把 `aiflow` 初始化到任意业务项目：

```bat
cd /d D:\some-project
aiflow init
aiflow context --compact
aiflow install-skills
aiflow verify --auto
```

一次典型 AI 编程任务：

```bat
aiflow context --compact
aiflow plan "实现用户提出的任务"
aiflow verify --auto --continue-on-error
aiflow review
```

## 一键安装

```bat
D:\code_work\aiflow-kit\scripts\quick-install.bat
```

该脚本会：

- 安装共享前端/Playwright 工具。
- 安装 Codex 与 Claude Code 用户级通用 Skills。
- 生成 Claude/Codex 插件包。
- 验证源码版 CLI 可运行。

它不会修改系统环境变量，不会写用户全局 `AGENTS.md` 或 `CLAUDE.md`，也不会把业务项目规则写到全局。

## 常用命令

| 命令 | 用途 |
| --- | --- |
| `aiflow init` | 初始化项目级代理规则和 `.aiflow/config.toml` |
| `aiflow context --compact` | 生成完整上下文和压缩上下文 |
| `aiflow memory list` | 查看项目级记忆 |
| `aiflow plan` | 生成或更新 `.aiflow/plan.md` |
| `aiflow verify --auto` | 自动推断并运行测试/构建命令 |
| `aiflow review` | 根据 git diff 生成交付前检查摘要 |
| `aiflow install-skills` | 安装内置 Skills 到当前项目 |
| `aiflow agents init` | 初始化多 Agent 协作工作区 |
| `aiflow agents plan` | 生成多 Agent 任务队列 |
| `aiflow forge detect` | 从 Git remote 识别 Gitee/GitHub 仓库 |
| `aiflow forge release create` | 创建 Gitee/GitHub Release |
| `aiflow browser serve` | 启动本地浏览器伴随插件 bridge |
| `aiflow db list` | 查看项目级数据库 profile |
| `aiflow claude-agent doctor` | 检查 Claude Agent SDK worker 配置 |

## Gitee/GitHub 发版自动化

推送 tag 只会创建 Git tag，不一定会创建平台上的“发行版”。`aiflow forge` 用来补上这一步。

```bat
aiflow forge detect
aiflow forge release create --provider gitee --repo aoxianglantian/aiflow-kit --tag v0.1.1 --name v0.1.1 --notes "Release notes"
aiflow forge release get --provider gitee --repo aoxianglantian/aiflow-kit --tag v0.1.1
```

GitHub 示例：

```bat
aiflow forge release create --provider github --repo owner/repo --tag v1.0.0 --name v1.0.0 --notes "Release notes"
```

Token 只从环境变量读取：

```powershell
$env:GITEE_ACCESS_TOKEN="..."
$env:GITHUB_TOKEN="..."
```

不要把 token 写进仓库、README、`.aiflow/memory.md` 或聊天记录。

## 目录结构

```text
aiflow-kit/
  src/aiflow/                 Python CLI 源码
  src/aiflow/assets/skills/   内置 Skills
  src/aiflow/assets/templates 项目模板
  scripts/                    Windows 包装与安装脚本
  docs/                       设计文档和专题指南
  extensions/browser/         Chrome/Edge 浏览器伴随插件
  node/claude-agent-runner/   Claude Agent SDK runner
  tests/                      CLI smoke tests
```

## 设计原则

- Skills 只放流程和判断标准，确定性扫描交给 CLI。
- 项目事实留在项目内，通用流程才进入用户级 Skills。
- 密钥和本地环境写入 `.aiflow/*.local.toml`，默认不提交。
- 先验证再交付，先 dry-run 再调用远程写接口。
- Windows 优先使用 `.bat` 辅助脚本，不依赖 PowerShell profile。
- 第一版不替代测试框架、不自动提交、不自动发 PR。

## 发版检查

发布前建议运行：

```bat
aiflow verify --auto --continue-on-error
aiflow review
python -m compileall src
python -m unittest discover -s tests
python -m pip wheel . -w dist
```

包版本在 `pyproject.toml` 和 `src/aiflow/__init__.py` 中维护。发布前请确认 CLI 版本、包版本、插件 manifest 版本、README 和 Release notes 一致。

## 文档

完整设计文档和专题指南见 [docs/README.md](docs/README.md)。

建议阅读：

- [13-快速安装](docs/13-快速安装.md)
- [03-Skills设计规范](docs/03-Skills设计规范.md)
- [17-多Agent协作流程](docs/17-多Agent协作流程.md)
- [21-记忆与上下文压缩](docs/21-记忆与上下文压缩.md)
- [22-Claude-Agent-SDK设计方案](docs/22-Claude-Agent-SDK设计方案.md)
- [23-浏览器伴随插件](docs/23-浏览器伴随插件.md)

## 许可证

本项目采用 Apache License 2.0。分发或修改时请保留 [LICENSE](LICENSE) 和 [NOTICE](NOTICE) 中的版权与作者信息。
