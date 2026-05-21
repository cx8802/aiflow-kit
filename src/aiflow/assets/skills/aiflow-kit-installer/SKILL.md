---
name: aiflow-kit-installer
description: Use when the user asks to install, initialize, add, enable, or set up aiflow-kit/aiflow in the current repository or another project, especially from Codex or Claude Code while working outside the aiflow-kit repository.
---

# AIFlow Kit Installer

## Source Path

The local `aiflow-kit` source repository is:

```text
D:\code_work\aiflow-kit
```

Use this wrapper to run the source version from any project:

```bat
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat
```

## Install Into Current Project

When the user says "install aiflow-kit in this project", run these commands from the target project root:

```bat
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat init
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat install-skills
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat context
```

This writes only project-level files:

```text
AGENTS.md
CLAUDE.md
.aiflow/config.toml
.aiflow/context.md
.agents/skills/
```

## Optional Current-Session Convenience

If the user wants the short `aiflow` command in the current `cmd` session:

```bat
set PATH=D:\code_work\aiflow-kit\scripts;%PATH%
aiflow --help
```

Do not use `setx` unless the user explicitly asks for a permanent user PATH change.

## Verify Install

After installing into the target project:

```bat
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat doctor
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat review
D:\code_work\aiflow-kit\scripts\aiflow-dev.bat verify --dry-run
```

## Safety Rules

- Install project rules and project skills into the current project only.
- Do not copy target project facts into global Codex or Claude Code config.
- Do not write database secrets into global config.
- Use `.aiflow/databases.local.toml` for project-local database secrets.
- Use `.bat` commands on Windows, not PowerShell `.ps1`.
