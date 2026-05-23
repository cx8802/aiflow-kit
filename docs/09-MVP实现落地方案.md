# MVP 实现落地方案

本文档把 `aiflow-kit` 从文档方案落到可运行代码。第一版只实现本地 CLI、内置模板和内置 Skills，不接 LLM、不接 MCP、不改用户全局配置。

## 实现范围

第一版实现：

- `aiflow init`
- `aiflow doctor`
- `aiflow context`
- `aiflow plan`
- `aiflow review`
- `aiflow verify`
- `aiflow install-skills`

项目文件扫描优先使用系统已安装的 `ripgrep`：

```bat
rg --files --hidden --glob !.git/**
```

如果 `rg` 不可用，CLI 自动回退到 Python 文件遍历。

第一版内置：

- `AGENTS.md` 模板
- `CLAUDE.md` 模板
- `.aiflow/config.toml` 模板
- 5 个核心流程 Skills 和 3 个 aiflow 全局辅助 Skills
- Claude Code 插件 manifest 模板
- Codex 插件 manifest 模板

## 代码结构

```text
aiflow-kit/
├── pyproject.toml
├── src/
│   └── aiflow/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── commands/
│       ├── core/
│       └── assets/
│           ├── templates/
│           └── skills/
├── scripts/
│   └── use-project-env.bat
└── docs/
```

模板和 Skills 放到 `packages/aiflow-cli/src/aiflow/assets/`，这样安装到项目 `.venv`（例如 `.venv\Scripts\python.exe -m pip install -e packages\aiflow-cli`）或后续打包安装后，CLI 仍能复制内置资源。

## 运行时分工

第一版不是所有能力都用 Python 实现。详细边界见 [10-运行时与脚本语言边界.md](10-运行时与脚本语言边界.md)。

| 能力 | 实现方式 |
| --- | --- |
| CLI 主控、模板复制、报告生成 | Python |
| Windows 当前会话环境隔离 | BAT |
| 文件清单扫描 | ripgrep，Python fallback |
| 前端依赖、构建、测试 | Node / `npm.cmd` / pnpm / yarn |
| Go 项目验证和后续高性能 helper | Go |
| JVM 项目验证 | Java / Maven |

## 命令优先级

第一批必须先能跑：

```bat
python -m aiflow --help
python -m aiflow init
python -m aiflow doctor
python -m aiflow install-skills
```

第二批：

```bat
python -m aiflow context
python -m aiflow review
python -m aiflow plan
```

第三批：

```bat
python -m aiflow verify --dry-run
python -m aiflow verify
```

安装后入口：

```bat
aiflow --help
```

## 安全边界

- `init` 只写当前项目。
- `install-skills` 默认只写当前项目 `.agents/skills/`。
- 用户级安装必须 `--confirm-global`，并且配置允许全局安装。
- `verify` 只运行 `.aiflow/config.toml` 显式配置的命令。
- CLI 不拼接用户输入到隐藏命令中；可执行命令只来自项目配置并会先打印。
- 不使用 `.ps1`，Windows 环境脚本只使用 `.bat`。
- 网络代理只通过 `scripts\use-project-env.bat proxy` 设置到当前 `cmd` 会话，默认不写全局代理。
- `ripgrep` 是性能增强，不是硬依赖；缺失时必须能回退。

## 验收命令

```bat
cd /d <aiflow-kit目录>
scripts\use-project-env.bat
python -m aiflow --help
python -m aiflow init
python -m aiflow doctor
python -m aiflow context
python -m aiflow review
python -m aiflow install-skills
python -m aiflow verify --dry-run
```

需要代理时：

```bat
scripts\use-project-env.bat proxy
```

## 后续增强

- 增加 JSON 输出。
- 增加更严格的污染扫描。
- 增加 Playwright 截图验证集成。
- 增加 Graphify 报告读取。
- 增加 CI 友好的 `--ci` 模式。
