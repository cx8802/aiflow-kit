# Superpowers 安装指南

## 简介

Superpowers 是一个完整的软件开发方法论插件，通过一系列可组合的 skills 让 AI 代理遵循结构化的开发流程。它能自动触发brainstorming、规划设计、TDD 等技能，避免直接跳入代码编写。

- **GitHub**: [obra/superpowers](https://github.com/obra/superpowers)
- **Stars**: 53k+
- **安装量**: 50k+

## 安装方式

### 方式一：官方插件命令安装（推荐）

在 Claude Code 中运行以下命令：

```bash
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

或直接从官方 marketplace 安装：

```bash
/plugin install superpowers@claude-plugins-official
```

### 方式二：手动安装

本项目已采用手动安装方式，skills 位于：
`C:\Users\15638\.claude\skills\`

已安装的 skills：
- brainstorming
- dispatching-parallel-agents
- executing-plans
- finishing-a-development-branch
- receiving-code-review
- requesting-code-review
- subagent-driven-development
- systematic-debugging
- test-driven-development
- using-git-worktrees
- using-superpowers
- verification-before-completion
- writing-plans
- writing-skills

## 核心 Skills

| Skill | 功能 |
|-------|------|
| **brainstorming** | 编码前的 Socratic 设计细化 |
| **writing-plans** | 详细的实现计划 |
| **test-driven-development** | 红-绿-重构 TDD 循环 |
| **executing-plans** | 分批执行并设置检查点 |
| **subagent-driven-development** | 快速迭代的两阶段审查 |
| **systematic-debugging** | 四阶段根因分析 |
| **requesting-code-review** | 按严重程度报告问题 |
| **finishing-a-development-branch** | 合并/PR 决策工作流 |

## 工作流程

1. **brainstorming** - 在写代码前激活，通过提问细化想法
2. **writing-plans** - 获得批准的设计后激活，将工作分解成小任务
3. **test-driven-development** - 实现过程中激活，强制 RED-GREEN-REFACTOR
4. **executing-plans** - 根据计划执行，分批处理并设置人工检查点
5. **requesting-code-review** - 任务之间激活，审查计划合规性
6. **finishing-a-development-branch** - 任务完成时激活，验证测试并提供选项

## 哲学理念

- **测试驱动开发** - 始终先写测试
- **系统化而非临时** - 流程优于猜测
- **复杂性降低** - 简单性作为主要目标
- **证据而非声明** - 在宣布成功前验证

## 使用方式

Superpowers 会自动检测相关技能并触发。也可以手动调用：

```bash
/superpowers:brainstorm
/superpowers:writing-plans
/superpowers:test-driven-development
```

## 参考资源

- [Superpowers GitHub](https://github.com/obra/superpowers)
- [官方文档](https://github.com/obra/superpowers#readme)
- [Blog 发布公告](https://blog.fsck.com/2025/10/09/superpowers/)
