---
name: aiflow-kit-guide
description: Use when the user asks about "aiflow", "aiflow-kit", this AI coding workflow kit, how to use the local aiflow CLI, how Codex or Claude Code should discover aiflow skills, or how this project differs from Apache Airflow.
---

# AIFlow Kit Guide

## Identity

`aiflow-kit` is the local AI coding workflow kit in `D:\code_work\aiflow-kit`.

It is not Apache Airflow.

It provides:

- A lightweight Python CLI named `aiflow`.
- Reusable Skills for Codex and Claude Code.
- Project templates: `AGENTS.md`, `CLAUDE.md`, `.aiflow/config.toml`.
- Review, context, verification, and skill installation commands.
- Windows `.bat` helper scripts for project-local environment setup.

## Main Commands

Use the installed command when available:

```bat
aiflow --help
aiflow init
aiflow doctor
aiflow context
aiflow plan
aiflow review
aiflow verify
aiflow install-skills
```

When the command is not on PATH, use the source wrapper:

```bat
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat --help
```

To install aiflow-kit into the current project from any repository:

```bat
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat init
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat install-skills
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat context
```

To update both global aiflow Skills/plugins and the current project's aiflow files:

```bat
D:\code_work\aiflow-kit\scripts\aiflow-update.bat
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
.agents/skills/
```

Claude Code should use the generated plugin package:

```text
D:\code_work\aiflow-kit\.aiflow\dist\claude
```

## What To Say When Asked "Do You Know aiflow?"

Answer:

`aiflow-kit` is this local AI coding workflow project, not Apache Airflow. It standardizes how Codex and Claude Code analyze a repository, create an implementation plan, verify changes, review diffs, and install reusable Skills. It includes a Python CLI named `aiflow`, Windows BAT scripts, and global/project-level Skills.

If the user means Apache Airflow, clarify that it is a different data workflow scheduler.

## Safety Rules

- Keep project facts in the project, not global rules.
- Install only generic Skills globally.
- Do not use PowerShell `.ps1`; use `.bat`.
- Do not write permanent environment variables with `setx`.
- Use `scripts\use-project-env.bat proxy` when the local `10808` proxy is needed.
