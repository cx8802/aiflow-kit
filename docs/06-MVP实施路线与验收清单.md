# MVP 实施路线与验收清单

本文档把第一版拆成可开发、可验收的任务。目标是先让流程跑通，再增强自动化。

## 阶段 0：文档定稿

产物：

- 文档索引。
- 双端适配架构。
- Skills 设计规范。
- CLI 与安装器规范。
- 插件分发流程。
- 全局与项目级边界。

验收：

- 新成员能从 `docs/README.md` 理解项目目标。
- 能明确 Claude Code 和 Codex 的不同目录结构。
- 能说明哪些内容可以全局安装，哪些必须留在项目内。
- 能按文档创建一个最小 Skill。

## 阶段 1：Skills 源文件

任务：

- 创建 `skills/project-analysis/SKILL.md`。
- 创建 `skills/implementation-plan/SKILL.md`。
- 创建 `skills/tdd-development/SKILL.md`。
- 创建 `skills/frontend-verify/SKILL.md`。
- 创建 `skills/code-review-release/SKILL.md`。

验收：

- 每个 Skill 有 `name` 和 `description`。
- 每个 Skill 有明确输入、流程和输出。
- 每个 Skill 少于 500 行。
- 不写死 Claude Code 或 Codex 专有工具名。
- 至少用 5 个触发 prompt 做人工检查。

## 阶段 2：项目模板

任务：

- 创建 `templates/AGENTS.md`。
- 创建 `templates/CLAUDE.md`。
- 创建 `templates/config.toml`。
- 创建 `templates/plan.md`。
- 创建 `templates/review.md`。
- 创建 `templates/verify.md`。

验收：

- `AGENTS.md` 和 `CLAUDE.md` 都保持短。
- 模板能指导 agent 调用 `aiflow context/review/verify`。
- `.aiflow/config.toml` 覆盖命令、frontend、review、skills 配置。
- 模板不得写入用户全局规则路径。

## 阶段 3：CLI 骨架

任务：

- 建立 Python 包结构。
- 实现 `aiflow --help`。
- 实现 `aiflow init`。
- 实现配置读写。
- 实现 Markdown 报告写入。

验收：

```bat
pip install -e .
aiflow --help
aiflow init
```

执行后生成：

```text
AGENTS.md
CLAUDE.md
.aiflow/config.toml
```

已有文件不被默认覆盖。

`aiflow init` 不修改用户全局 `AGENTS.md`、`CLAUDE.md`、Codex/Claude 配置或全局 skills 目录。

## 阶段 4：上下文与 review

任务：

- 实现 `aiflow context`。
- 实现 `aiflow review`。
- 实现基础风险规则。

验收：

```bat
aiflow context
aiflow review
```

执行后生成：

```text
.aiflow/context.md
.aiflow/review.md
```

`review.md` 至少包含 changed files、diff stat、高风险路径、测试信号。

## 阶段 5：验证命令

任务：

- 实现 `aiflow doctor`。
- 实现 `aiflow verify`。
- 支持 `--dry-run`。
- 支持 `--continue-on-error`。

验收：

```bat
aiflow doctor
aiflow verify --dry-run
aiflow verify
```

要求：

- 未配置命令时不猜测执行。
- 已配置命令时记录退出码。
- 失败命令写入 `.aiflow/verify.md`。

## 阶段 6：安装器和插件包

任务：

- 实现 `aiflow install-skills --target codex-repo`。
- 实现 `aiflow install-skills --target codex-user`。
- 实现 `aiflow install-skills --target claude-user`。
- 实现 `aiflow install-skills --target claude-plugin`。
- 实现 `aiflow install-skills --target codex-plugin`。
- 生成两个插件 manifest。

验收：

```bat
aiflow install-skills --target codex-repo
aiflow install-skills --target codex-user --confirm-global --allow-global
aiflow install-skills --target claude-user --confirm-global --allow-global
aiflow install-skills --target claude-plugin --output .aiflow/dist/claude
aiflow install-skills --target codex-plugin --output .aiflow/dist/codex
```

生成目录：

```text
.agents/skills/
.aiflow/dist/claude/.claude-plugin/plugin.json
.aiflow/dist/codex/.codex-plugin/plugin.json
```

要求：

- 无参数安装默认只写当前项目。
- `codex-user`、`claude-user` 等用户级安装必须要求 `--confirm-global --allow-global`。
- 全局安装前执行污染检查，拒绝包含项目事实的内容。
- 安装报告标明 scope：`project`、`user` 或 `team`。

## 阶段 7：真实项目试跑

至少选择两个项目：

- 一个前端项目。
- 一个后端或 CLI 项目。

试跑路径：

```text
aiflow init
aiflow doctor
aiflow context
触发 project-analysis
触发 implementation-plan
实现一个小功能或 bugfix
aiflow verify
aiflow review
触发 code-review-release
```

验收：

- 前端项目有 UI 验证记录。
- 后端项目有测试命令记录。
- review 能指出至少一种真实风险或确认无明显问题。
- 用户能根据输出写 PR 描述。

## 质量门槛

合入 MVP 前必须满足：

- Windows `cmd` / `.bat` 可用，不依赖 PowerShell `.ps1`。
- 路径处理支持空格。
- 不覆盖用户已有文件。
- 不污染用户全局规则、全局配置或全局 skills 目录。
- 不执行未配置的验证命令。
- CLI 报错信息包含下一步建议。
- 文档中的命令能在空仓库或最小仓库中跑通。

## 后续增强

MVP 稳定后再考虑：

- JSON 输出。
- GitHub PR 描述生成。
- Playwright 截图命令自动发现。
- Graphify 深度集成。
- MCP server 包装。
- 团队 marketplace 发布。
- CI 中运行 `aiflow review --ci`。
