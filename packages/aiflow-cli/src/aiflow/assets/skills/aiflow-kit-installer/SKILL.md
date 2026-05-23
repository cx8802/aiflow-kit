---
name: aiflow-kit-installer
description: Use when the user asks to install, initialize, add, enable, or set up aiflow-kit/aiflow in the current repository or another project, especially from Codex or Claude Code while working outside the aiflow-kit repository.
---

# AIFlow Kit Installer

## Source Path

The local `aiflow-kit` source repository is:

```text
{{ AIFLOW_KIT_ROOT }}
```

Use this wrapper to run the source version from any project:

```bat
{{ AIFLOW_DEV_BAT }}
```

On macOS / Linux, use:

```sh
sh {{ AIFLOW_KIT_ROOT }}/scripts/mac/aiflow-dev.sh
```

## Install Into Current Project

When the user says "install aiflow-kit in this project", prefer the one-command launcher from the target project root.

Windows:

```bat
{{ AIFLOW_KIT_ROOT }}\scripts\win\aiflow-install.bat
```

macOS / Linux:

```sh
sh {{ AIFLOW_KIT_ROOT }}/scripts/mac/aiflow-install.sh
```

If you need to avoid touching existing project rule files, use:

```bat
{{ AIFLOW_KIT_ROOT }}\scripts\win\aiflow-install.bat --skip-rules
```

```sh
sh {{ AIFLOW_KIT_ROOT }}/scripts/mac/aiflow-install.sh --skip-rules
```

The launcher runs the equivalent project-level setup:

```bat
{{ AIFLOW_DEV_BAT }} init
{{ AIFLOW_DEV_BAT }} install-skills
{{ AIFLOW_DEV_BAT }} env detect
{{ AIFLOW_DEV_BAT }} context --compact
{{ AIFLOW_DEV_BAT }} verify --auto --dry-run
```

This writes only project-level files:

```text
AGENTS.md
CLAUDE.md
.aiflow/config.toml
.aiflow/context.md
.aiflow/context.compact.md
.agents/skills/
```

Playwright runtime packages and browser downloads stay in the shared `aiflow-kit` `.tools/` directory.
`.aiflow/memory.md` is created later by `aiflow memory add`.

## Optional Current-Session Convenience

If the user wants the short `aiflow` command in the current `cmd` session:

```bat
call {{ AIFLOW_KIT_ROOT }}\scripts\win\aiflow-env.bat
aiflow --help
aiflow-install
```

If the user wants the short `aiflow` command in the current macOS / Linux shell session:

```sh
. {{ AIFLOW_KIT_ROOT }}/scripts/mac/aiflow-env.sh
aiflow --help
aiflow-install
```

Do not use `setx`, `launchctl setenv`, or shell profile edits unless the user explicitly asks for a permanent user PATH change.

## Verify Install

After installing into the target project:

```bat
{{ AIFLOW_DEV_BAT }} doctor
{{ AIFLOW_DEV_BAT }} review
{{ AIFLOW_DEV_BAT }} verify --dry-run
```

## Safety Rules

- Install project rules and project skills into the current project only.
- Do not copy target project facts into global Codex or Claude Code config.
- Do not write database secrets into global config.
- Use `.aiflow/databases.local.toml` for project-local database secrets.
- Use `.bat` commands on Windows, not PowerShell `.ps1`.
- Use `.sh` commands on macOS / Linux, and keep environment changes scoped to the current shell unless the user explicitly asks for permanent setup.
