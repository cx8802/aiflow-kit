# Codex 与 Claude Code 全局接入

如果只在某个项目里生成 `.agents/skills/`、`AGENTS.md`、`CLAUDE.md`，Codex 和 Claude Code 只有进入这个项目时才知道 `aiflow`。如果希望它们在任意项目中都知道有 `aiflow` 这套通用流程，需要一个全局接入层。

全局接入只放通用能力：

- 5 个流程 Skills。
- 1 个 `aiflow-kit-guide` 说明 Skill，用于回答“aiflow/aiflow-kit 是什么”。
- 1 个 `aiflow-kit-installer` 安装 Skill，用于在其他项目中通过 Codex/Claude 安装 aiflow-kit。
- 插件 manifest。
- 指向 `aiflow` CLI 的使用说明。

全局接入不能放：

- 某个项目的 `.aiflow/context.md`。
- 某个项目的测试、构建、启动命令。
- 某个项目的风险路径。
- 某个项目的业务规则。
- token、内网地址、某个项目的临时代理环境变量。

可以放入全局接入的是通用网络策略：访问中国网站直连，访问中国以外的网站按需使用 `http://127.0.0.1:10808`，不要把代理环境变量永久写入系统。

## Codex 推荐方式

Codex 可以读取用户级 Skills。把通用 aiflow Skills 安装到用户级目录后，Codex 在其他项目也能发现这些 Skills。

命令：

```bat
cd /d <aiflow-kit目录>
scripts\aiflow-dev.bat install-skills --target codex-user --confirm-global --allow-global
```

目标目录：

```text
%USERPROFILE%\.agents\skills\
├── aiflow-kit-guide\
├── aiflow-kit-installer\
├── project-analysis\
├── implementation-plan\
├── tdd-development\
├── frontend-verify\
└── code-review-release\
```

这一步是全局安装，所以必须显式写：

```text
--confirm-global --allow-global
```

安装后建议重启 Codex，让它重新扫描 Skills。

## Claude Code 推荐方式

Claude Code 有两种接入方式：

1. 用户级 standalone Skills：`%USERPROFILE%\.claude\skills`
2. 插件包：`.claude-plugin/plugin.json` + `skills/`

快速全局接入可以先安装用户级 Skills：

```bat
cd /d <aiflow-kit目录>
scripts\aiflow-dev.bat install-skills --target claude-user --confirm-global --allow-global
```

目标目录：

```text
%USERPROFILE%\.claude\skills\
```

如果要使用插件方式，再生成本地插件包：

```bat
cd /d <aiflow-kit目录>
scripts\aiflow-dev.bat install-skills --target claude-plugin --output .aiflow\dist\claude
```

生成：

```text
.aiflow/dist/claude/
├── .claude-plugin/plugin.json
└── skills/
```

本地测试可以使用 Claude Code 的插件目录参数：

```bat
claude --plugin-dir <aiflow-kit目录>\.aiflow\dist\claude
```

如果要长期团队分发，应通过 Claude Code 的插件安装/marketplace 机制安装这个插件包。不要把某个项目的 `CLAUDE.md` 复制到全局。

## CLI 怎么让 Codex / Claude 调用

Skills 会告诉 agent 可以运行：

```bat
aiflow context
aiflow review
aiflow verify
```

如果在其他项目中还没有 `aiflow` 命令，安装 Skill 会告诉 agent 使用源码路径：

```bat
%AIFLOW_KIT%\scripts\aiflow-dev.bat init
%AIFLOW_KIT%\scripts\aiflow-dev.bat install-skills
%AIFLOW_KIT%\scripts\aiflow-dev.bat context
```

所以还需要让 `aiflow` 命令在终端可用。开发期有三种方式：

方式一：当前会话 PATH：

```bat
set PATH=%AIFLOW_KIT%\scripts;%PATH%
aiflow --help
```

方式二：源码版全路径：

```bat
%AIFLOW_KIT%\scripts\aiflow-dev.bat --help
```

方式三：安装到 `.venv`：

```bat
cd /d <aiflow-kit目录>
scripts\use-project-env.bat
.venv\Scripts\python.exe -m pip install -e packages\aiflow-cli
aiflow --help
```

如果希望 Codex/Claude Code 在任意项目都能直接调用 `aiflow`，需要选择方式一的用户 PATH 版或方式三的稳定安装版。但这属于用户级接入，应等项目命令稳定后再做。

## 推荐落地顺序

1. 先在 `aiflow-kit` 本项目验证 CLI。
2. 给一个试点项目运行 `aiflow init` 和 `aiflow install-skills`。
3. 确认全局 Skills 没有项目特定内容。
4. 安装 Codex 用户级 Skills。
5. 安装 Claude Code 用户级 Skills。
6. 生成 Claude Code 插件包并本地测试。
7. 稳定后再做 Claude marketplace。

在其他项目中安装的完整说明见 [16-在其他项目中安装aiflow-kit.md](16-在其他项目中安装aiflow-kit.md)。

## 一句话结论

- Codex 要全局知道 aiflow：安装通用 Skills 到 `%USERPROFILE%\.agents\skills`。
- Claude Code 要全局知道 aiflow：安装通用 Skills 到 `%USERPROFILE%\.claude\skills`，或生成并安装 aiflow 插件包。
- 两者要能调用 CLI：还需要让 `aiflow` 命令在终端 PATH 中可用。
- 项目事实仍然只放具体项目，不放全局。
