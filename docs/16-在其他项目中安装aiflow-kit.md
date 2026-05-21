# 在其他项目中安装 aiflow-kit

本项目已经提供全局 Skill：`aiflow-kit-installer`。

它的作用是让 Codex / Claude Code 在其他项目中也知道：

```text
aiflow-kit 源码路径 = D:\code_work\aiflow-kit
```

当用户在任意项目中说：

```text
帮我在这个项目安装 aiflow-kit
```

agent 应该从当前项目根目录调用：

```bat
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat init
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat install-skills
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat context --compact
```

## 安装后生成什么

目标项目会生成：

```text
AGENTS.md
CLAUDE.md
.aiflow/
├── config.toml
├── context.md
└── context.compact.md
.agents/
└── skills/
    ├── aiflow-kit-guide/
    ├── aiflow-kit-installer/
    ├── project-analysis/
    ├── implementation-plan/
    ├── tdd-development/
    ├── frontend-design/
    ├── frontend-verify/
    ├── playwright-verify/
    └── code-review-release/
```

注意：项目级安装不会写入用户全局目录。
Playwright 运行时工具复用 `aiflow-kit/.tools/`，不会在目标项目里再安装一份。
`.aiflow/memory.md` 会在第一次执行 `aiflow memory add` 时创建。

## 当前会话快捷方式

如果用户希望在当前 `cmd` 里直接输入 `aiflow`：

```bat
set PATH=D:\code_work\aiflow-kit\scripts;%PATH%
aiflow --help
```

不要默认执行：

```bat
setx PATH ...
```

永久 PATH 修改必须等用户明确要求。

## 验证安装

在目标项目里运行：

```bat
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat doctor
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat review
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat verify --dry-run
```

如果已经把 `scripts` 加入当前会话 PATH：

```bat
aiflow doctor
aiflow review
aiflow verify --dry-run
```

## 数据库连接

如果安装后用户在会话中提供数据库连接，保存到目标项目：

```bat
aiflow db add dev --type postgres --dsn "postgres://user:password@127.0.0.1:5432/app" --secret-local
```

敏感信息会写入：

```text
.aiflow/databases.local.toml
```

该文件应被 `.gitignore` 忽略。

## 给 Codex / Claude Code 的执行规则

1. 先确认当前目录是目标项目根目录。
2. 使用 `D:\code_work\aiflow-kit\scripts\aiflow-dev.bat`，不要猜测 aiflow 是否在 PATH。
3. 默认执行项目级安装，不做全局安装。
4. 不复制目标项目事实到全局 Skills。
5. 不保存数据库 secret 到 `.aiflow/databases.toml`。
6. 安装完成后提示用户重启 Codex/Claude Code 只在需要重新读取全局 Skills 时才必要；项目级文件当前会话可直接读取。

## 推荐提示词

用户可以在其他项目中这样说：

```text
使用全局 aiflow-kit-installer，帮我在当前项目安装 aiflow-kit，并生成 context。
```

或者：

```text
这个项目接入 aiflow-kit，使用 D:\code_work\aiflow-kit 的源码版安装。
```

## 更新全局和当前项目

如果用户在其他项目中说：

```text
帮我更新下 aiflow
```

agent 应执行：

```bat
D:\code_work\aiflow-kit\scripts\aiflow-update.bat
```

它会同时更新：

- Codex 用户级 aiflow Skills。
- Claude Code 用户级 aiflow Skills。
- Claude Code 插件包。
- Codex 插件包。
- 当前项目 `.agents/skills`。
- 当前项目 `.aiflow/context.md`。
- `aiflow-kit` 共享 `.tools/frontend-tools` 和 `.tools/ms-playwright`。

更新全局 Skills 或插件后，可能需要重启 Codex / Claude Code。
