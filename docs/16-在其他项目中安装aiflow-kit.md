# 在其他项目中安装 aiflow-kit

`aiflow-kit` 的目标是把项目规则、上下文、Skills 和验证记录安装到目标项目本身，而不是写入用户全局目录。

## 推荐方式

Windows 先在当前 CMD 会话启用短命令：

```bat
call F:\code_work\aiflow-kit\scripts\win\aiflow-env.bat
```

然后进入目标项目：

```bat
cd /d <目标项目目录>
aiflow-install
```

macOS / Linux 先在当前 shell 会话启用短命令：

```sh
. /path/to/aiflow-kit/scripts/mac/aiflow-env.sh
```

然后进入目标项目：

```sh
cd <目标项目目录>
aiflow-install
```

如果目标项目已经有自己的 `AGENTS.md` 和 `CLAUDE.md`，避免生成规则文件：

```bat
aiflow-install --skip-rules
```

## 直接路径方式

不想配置当前 CMD 会话时，也可以直接运行：

```bat
F:\code_work\aiflow-kit\scripts\win\aiflow-install.bat
```

macOS / Linux 直接路径方式：

```sh
sh /path/to/aiflow-kit/scripts/mac/aiflow-install.sh
```

平台脚本分开放在 `scripts/win/` 和 `scripts/mac/`，`scripts/` 根目录不放命令脚本。

## 安装后生成什么

默认会在目标项目生成或刷新：

```text
AGENTS.md 或 AGENTS.md.new
CLAUDE.md 或 CLAUDE.md.new
.aiflow/config.toml
.aiflow/env.local.toml
.aiflow/context.md
.aiflow/context.compact.md
.aiflow/verify.md
.agents/skills/
```

如果使用 `--skip-rules`，不会创建 `AGENTS.md` / `CLAUDE.md`。

## 安全边界

- 默认只写当前项目。
- 不写 `%USERPROFILE%\.agents\skills`。
- 不写 `%USERPROFILE%\.claude\skills`。
- 不使用 `setx` 修改永久用户环境变量。
- 不写 `~/.zshrc`、`~/.bashrc` 或 `launchctl setenv` 修改 macOS / Linux 永久用户环境。
- 不把目标项目事实复制到全局 Skills。
- 数据库、Token、内网地址等敏感信息只允许写入项目级 local 文件。

## 验证安装

安装脚本会自动运行：

```bat
aiflow verify --auto --dry-run
```

需要手动检查时可以运行：

```bat
aiflow doctor
aiflow review
aiflow verify --dry-run
```

## 给 Agent 的执行规则

1. 先确认当前目录是目标项目根目录。
2. 优先运行 `aiflow-install`。
3. 如果目标项目已有自己的规则文件，使用 `aiflow-install --skip-rules`。
4. 不做用户级全局安装，除非用户显式要求。
5. 安装完成后说明生成了哪些项目级文件，以及验证命令结果。
