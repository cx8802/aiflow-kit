# 多 Agent 协作流程

`aiflow-kit` 的多 Agent 能力不是一个后台服务，而是一套项目级协作协议。Codex、Claude Code、多个会话或支持 sub-agent 的工具，都可以围绕同一组文件协作。

## 目标

- 把大任务拆成可并行的探索、实现、验证、评审任务。
- 明确每个 Agent 的角色、写入范围和交付格式。
- 避免多个 Agent 同时修改同一批文件造成冲突。
- 把项目事实、任务状态和交接内容保存在当前项目。
- 让 Codex 和 Claude Code 都能读懂同一套工作流。

## 文件结构

```text
.aiflow/agents/
├── roles.toml
├── status.md
├── handoff.md
└── tasks/
    ├── 001-explore-<goal>.md
    ├── 002-implement-<goal>.md
    ├── 003-verify-<goal>.md
    └── 004-review-<goal>.md
```

这些文件都是项目级的。不要把 `tasks/`、`status.md`、`handoff.md` 复制到用户全局配置。

## 命令

初始化多 Agent 工作区：

```bat
aiflow agents init
```

按目标生成任务队列：

```bat
aiflow agents plan "实现订单导出并补测试"
```

查看当前状态：

```bat
aiflow agents status
```

生成或刷新交接文件：

```bat
aiflow agents handoff "实现订单导出并补测试" --force
```

## 角色

| 角色 | 职责 | 是否写代码 |
| --- | --- | --- |
| orchestrator | 拆任务、定边界、分配 owner、整合结果 | 只在需要整合时写 |
| explorer | 只读分析代码、影响面、风险、命令 | 否 |
| worker | 在明确 write scope 内实现或补测试 | 是 |
| reviewer | 审查 diff、验证结果、风险和交付摘要 | 通常否 |

## 全局与项目级边界

可以全局安装：

- `multi-agent-orchestrator`
- `multi-agent-explorer`
- `multi-agent-worker`
- `multi-agent-reviewer`
- 角色职责、输出契约、冲突规避规则

必须留在项目内：

- 具体任务目标
- 代码结构和业务事实
- 数据库连接、token、内网地址
- 某次任务的状态、结果、风险和交接
- 具体测试、构建、部署命令

## Codex 使用方式

当用户明确要求多 Agent、并行 Agent、分工执行时，Codex 可以把 `.aiflow/agents/tasks/` 里的任务映射到 sub-agent。

原则：

- 先由 orchestrator 生成任务和 write scope。
- explorer 任务保持只读。
- worker 任务必须有不重叠的写入范围。
- reviewer 在实现后检查 diff 和验证结果。
- 最终结果写回 `.aiflow/agents/handoff.md`。

## Claude Code 使用方式

Claude Code 可以通过多个会话或插件 Skills 读取同一套 `.aiflow/agents/` 文件：

- 一个会话作为 orchestrator。
- 一个或多个会话处理 explorer / worker 任务。
- 最后由 reviewer 会话读取 handoff 和 diff。

因为任务协议是文件化的，所以不依赖某个工具的私有多 Agent API。

## 冲突规避规则

- 不给两个 worker 分配同一文件或同一模块的写入权限。
- worker 不能回滚用户或其他 Agent 的修改。
- 如果发现未授权范围内的必要改动，先写入 handoff 或报告 blocker。
- reviewer 优先找 bug、遗漏测试、跨任务集成风险。
- orchestrator 负责最终合并和验证。

## 推荐流程

```text
理解目标
-> aiflow agents plan
-> explorer 并行分析
-> orchestrator 收敛方案
-> worker 分片实现
-> verifier 跑测试
-> reviewer 审查
-> handoff 汇总
```

## 当前实现能力

- `aiflow agents init`：生成 `roles.toml`、`status.md`、`handoff.md` 和 `tasks/`。
- `aiflow agents plan`：按目标生成 4 个默认任务。
- `aiflow agents status`：汇总当前多 Agent 工作区。
- `aiflow agents handoff`：生成交接模板。
- 内置 4 个多 Agent Skills，可安装到 Codex / Claude 全局或项目级 Skills。
