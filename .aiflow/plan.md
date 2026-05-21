# Plan: multi database connection support

## Goal

Extend `aiflow db` so project-level database profiles can be tested and inspected across common database engines, not only SQLite.

## Non-goals

- Do not store database secrets in global Codex or Claude configuration.
- Do not make heavyweight database drivers mandatory dependencies of `aiflow-kit`.
- Do not install system ODBC drivers or vendor clients automatically.

## Impact scope

- `src/aiflow/core/databases.py`
- `src/aiflow/commands/db.py`
- `tests/test_cli_smoke.py`
- `docs/15-数据库连接项目级配置.md`

## Steps

1. Add profile resolution that merges tracked config, local secrets, and environment variables.
2. Add optional-driver connection tests for MySQL, PostgreSQL, SQL Server, Oracle, MongoDB, and SQLite.
3. Add `aiflow db tables <name>` for listing tables or collections when the selected driver is installed.
4. Add smoke tests for new command behavior without requiring live database services.
5. Update docs with project-local driver install commands, proxy use, and global/project boundaries.

## Verification

- `python -m compileall -q src tests`
- `python -m unittest discover -s tests`
- Live regression against the configured `zhihaoscm` MySQL profile when available.
