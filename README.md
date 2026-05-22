# aiflow-kit

`aiflow-kit` 是一个轻量级 AI 编程工作流工具包，用 CLI、项目模板和 Skills，把一次 AI 编程任务稳定拆成：

```text
理解项目 -> 制定计划 -> 编码实现 -> 验证结果 -> 评审交付 -> 复盘沉淀
```

它面向同时使用 Codex、Claude Code 或多 Agent 协作的开发者，重点不是替代 IDE 或测试框架，而是把“项目上下文、执行边界、验证命令、交付检查”沉淀到仓库里，让 AI 代理每次都从同一套项目事实出发。

## 核心能力

- 项目初始化：生成 `AGENTS.md`、`CLAUDE.md` 和 `.aiflow/config.toml`，把代理规则留在当前项目。
- 上下文压缩：生成 `.aiflow/context.md` 和 `.aiflow/context.compact.md`，降低重复读仓库的成本。
- 项目记忆：用 `aiflow memory` 保存可复用事实，默认写入项目内，不写用户全局配置。
- Skills 分发：内置分析、计划、TDD、前端验证、发布评审、多 Agent 等工作流 Skills。
- 验证与评审：用 `aiflow verify`、`aiflow review` 固化测试、构建和交付前检查。
- 多 Agent 协作：用 `.aiflow/agents/` 维护任务队列、角色分工、handoff 和状态。
- 伴随工具：支持浏览器上下文采集、项目级数据库 profile、WSL/SSH 操作入口、Claude Agent SDK worker。

## 安装

### 源码运行

```bat
cd /d D:\code_work\aiflow-kit
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python -m aiflow --help
```

仓库提供了 Windows 包装脚本：

```bat
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat --help
```

如果想在当前终端直接使用 `aiflow`：

```bat
set PATH=D:\code_work\aiflow-kit\scripts;%PATH%
aiflow --help
```

### 一键安装 Skills 和插件包

```bat
D:\code_work\aiflow-kit\scripts\quick-install.bat
```

该脚本会安装共享前端/Playwright 工具，安装 Codex 与 Claude Code 用户级 Skills，并生成 Claude/Codex 插件包。它不会修改系统环境变量，不会写用户全局 `AGENTS.md` 或 `CLAUDE.md`，也不会把业务项目规则写到全局。

## 快速开始

在任意业务项目中初始化 aiflow：

```bat
cd /d D:\some-project
aiflow init
aiflow context --compact
aiflow verify --auto
```

推荐一次任务的基础流程：

```bat
aiflow context --compact
aiflow plan "说明本次任务目标"
aiflow verify --auto --continue-on-error
aiflow review
```

如果要把内置 Skills 安装到当前项目：

```bat
aiflow install-skills
```

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
| `aiflow browser serve` | 启动本地浏览器伴随插件 bridge |
| `aiflow db list` | 查看项目级数据库 profile |
| `aiflow claude-agent doctor` | 检查 Claude Agent SDK worker 配置 |

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

## 配置边界

`aiflow-kit` 的默认原则是项目事实留在项目内：

- 项目规则写入当前仓库的 `AGENTS.md`、`CLAUDE.md` 和 `.aiflow/`。
- 可复用项目事实写入 `.aiflow/memory.md`，不要保存密钥。
- 密钥和本地环境写入 `.aiflow/*.local.toml`，这些文件默认被 `.gitignore` 忽略。
- 用户级 Skills 安装需要显式确认，避免把某个项目的规则污染到所有项目。

## 发版检查

发版前建议运行：

```bat
aiflow verify --auto --continue-on-error
aiflow review
python -m compileall src
python -m unittest discover -s tests
```

当前包版本在 `pyproject.toml` 和 `src/aiflow/__init__.py` 中维护。发布前请确认版本号、README、验证记录和插件 manifest 版本一致。

## 文档

完整设计文档和专题指南见 [docs/README.md](docs/README.md)。建议从快速安装、CLI 与模板安装器、Skills 设计规范、多 Agent 协作流程、记忆与上下文压缩开始读。

## 许可证

当前仓库尚未声明许可证。对外发布前请先补充 `LICENSE`。
