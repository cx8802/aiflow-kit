---
name: aiflow-kit-guide
description: Use when the user asks about "aiflow", "aiflow-kit", this AI coding workflow kit, how to use the local aiflow CLI, how Codex or Claude Code should discover aiflow skills, or how this project differs from Apache Airflow.
---

# AIFlow Kit Guide

## Identity

`aiflow-kit` is the local AI coding workflow kit in `{{ AIFLOW_KIT_ROOT }}`.

It is not Apache Airflow.

It provides:

- A lightweight Python CLI named `aiflow`.
- Reusable Skills for Codex and Claude Code.
- Project templates: `AGENTS.md`, `CLAUDE.md`, `.aiflow/config.toml`.
- Review, context, verification, and skill installation commands.
- Project-level multi-agent coordination files under `.aiflow/agents/`.
- Windows `.bat` helper scripts for project-local environment setup.

## Main Commands

Use the installed command when available:

```bat
aiflow --help
aiflow init
aiflow doctor
aiflow context
aiflow context --compact
aiflow compact
aiflow memory list
aiflow memory search "keyword"
aiflow plan
aiflow review
aiflow verify
aiflow verify --auto
aiflow config check
aiflow config show
aiflow frontend install
aiflow claude-agent doctor
aiflow claude-agent run "task" --model small --dry-run
aiflow install-skills
aiflow agents init
aiflow agents plan "goal"
aiflow agents status
aiflow agents start <task-id>
aiflow agents done <task-id>
```

When the command is not on PATH, use the source wrapper:

```bat
{{ AIFLOW_DEV_BAT }} --help
```

To install aiflow-kit into the current project from any repository:

```bat
{{ AIFLOW_DEV_BAT }} init
{{ AIFLOW_DEV_BAT }} install-skills
{{ AIFLOW_DEV_BAT }} context --compact
```

To update both global aiflow Skills/plugins and the current project's aiflow files:

```bat
{{ AIFLOW_UPDATE_BAT }}
```

## Discovery Model

Codex can discover generic aiflow skills from:

```text
%USERPROFILE%\.agents\skills\
```

Project-specific setup is generated inside each target project:

```text
AGENTS.md
CLAUDE.md
.aiflow/config.toml
.aiflow/context.md
.aiflow/context.compact.md
.aiflow/memory.md
.aiflow/agents/
.agents/skills/
```

Claude Code should use the generated plugin package:

```text
{{ AIFLOW_CLAUDE_PLUGIN_DIR }}
```

## What To Say When Asked "Do You Know aiflow?"

Answer:

`aiflow-kit` is this local AI coding workflow project, not Apache Airflow. It standardizes how Codex and Claude Code analyze a repository, create an implementation plan, verify changes, review diffs, and install reusable Skills. It includes a Python CLI named `aiflow`, Windows BAT scripts, and global/project-level Skills.

If the user means Apache Airflow, clarify that it is a different data workflow scheduler.

## Safety Rules

- Keep project facts in the project, not global rules.
- Install only generic Skills globally.
- Use project memory for reusable project facts; use global memory only for explicit user preferences.
- Do not store secrets in memory files.
- Do not use PowerShell `.ps1`; use `.bat`.
- Do not write permanent environment variables with `setx`.
- Network proxy policy is global for aiflow work: access China websites directly; access non-China websites through `http://127.0.0.1:10808` when network access is needed.
- Do not enable `HTTP_PROXY`/`HTTPS_PROXY` for every command by default. Use proxy only for non-China resources such as GitHub, OpenAI, npmjs.org, Maven Central, Docker Hub, and other overseas services.
- Prefer direct access for China resources such as Gitee, Aliyun, Tencent Cloud, Baidu, Huawei Cloud, Tsinghua/USTC mirrors, `npmmirror.com`, and `.cn` domains.
- For one project/session that needs overseas access, use `scripts\use-project-env.bat proxy`; keep proxy settings scoped to the current `cmd` session.
