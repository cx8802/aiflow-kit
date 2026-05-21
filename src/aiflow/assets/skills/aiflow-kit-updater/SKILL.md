---
name: aiflow-kit-updater
description: Use when the user asks to update, refresh, reinstall, upgrade, or sync aiflow/aiflow-kit globally and in the current project from Codex or Claude Code.
---

# AIFlow Kit Updater

## Source Path

The local `aiflow-kit` source repository is:

```text
D:\code_work\aiflow-kit
```

## Update Global and Current Project

When the user says "update aiflow" or "update aiflow-kit" from another project, run this from the current project root:

```bat
D:\code_work\aiflow-kit\scripts\aiflow-update.bat
```

This updates:

- Codex user-level Skills in `%USERPROFILE%\.agents\skills`.
- Claude Code plugin package in `D:\code_work\aiflow-kit\.aiflow\dist\claude`.
- Codex plugin package in `D:\code_work\aiflow-kit\.aiflow\dist\codex`.
- Current project `AGENTS.md`, `CLAUDE.md`, `.aiflow/config.toml` when missing.
- Current project `.agents/skills`.
- Current project `.aiflow/context.md`.

## Safety Rules

- Do not write project facts to global Skills.
- Do not overwrite project rules with `--force` unless the user explicitly asks.
- Project Skills may be overwritten because they are generated from aiflow-kit.
- Restart Codex or Claude Code after global updates if they need to reload Skills/plugins.
