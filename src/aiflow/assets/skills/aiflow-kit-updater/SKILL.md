---
name: aiflow-kit-updater
description: Use only when the user explicitly asks to update, refresh, reinstall, upgrade, or sync aiflow/aiflow-kit from Codex or Claude Code. Do not use for generic requests like "update this", "更新下", or "同步一下" unless the user names aiflow/aiflow-kit.
---

# AIFlow Kit Updater

## Source Path

The local `aiflow-kit` source repository is:

```text
{{ AIFLOW_KIT_ROOT }}
```

## Update Global Skills and Plugins

When the user says "update aiflow" or "update aiflow-kit", run:

```bat
{{ AIFLOW_UPDATE_BAT }}
```

By default this updates:

- Codex user-level Skills in `%USERPROFILE%\.agents\skills`.
- Claude Code plugin package in `{{ AIFLOW_CLAUDE_PLUGIN_DIR }}`.
- Codex plugin package in `{{ AIFLOW_CODEX_PLUGIN_DIR }}`.

It does not create or refresh files in the current project by default.

## Update Current Project Too

Only when the user explicitly asks to install, enable, initialize, or update aiflow/aiflow-kit in the current project, run:

```bat
{{ AIFLOW_UPDATE_BAT }} --with-project
```

This also updates:

- Current project `AGENTS.md`, `CLAUDE.md`, `.aiflow/config.toml` when missing.
- Current project `.agents/skills`.
- Current project `.aiflow/context.md`.

## Safety Rules

- Do not use this skill for generic update requests unless the user explicitly names aiflow or aiflow-kit.
- Do not create project-level aiflow files unless the user explicitly asks for current-project aiflow setup or passes `--with-project`.
- Do not write project facts to global Skills.
- Do not overwrite project rules with `--force` unless the user explicitly asks.
- Project Skills may be overwritten because they are generated from aiflow-kit.
- Restart Codex or Claude Code after global updates if they need to reload Skills/plugins.
