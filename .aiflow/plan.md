# Implementation Plan

## Goal

Add a general `aiflow db query` command so database profiles can run arbitrary project-requested queries instead of only connection tests and table listings.

## Current Support

- Profile management: `aiflow db add/list/show`
- Health check: `aiflow db test`
- Metadata listing: `aiflow db tables`
- Database types: `sqlite`, `mysql`, `postgres`, `sqlserver`, `oracle`, `mongodb`

## Impact Scope

- `src/aiflow/commands/db.py`
- `src/aiflow/core/databases.py`
- `tests/test_cli_smoke.py`
- `docs/15-数据库连接项目级配置.md`

## Steps

1. Add smoke tests for `aiflow db query` using SQLite.
2. Add CLI parser support for SQL text, row limit, and output format.
3. Implement query execution for SQLite, MySQL, PostgreSQL, SQL Server, Oracle, and MongoDB.
4. Print result rows for returning queries and affected row counts for non-returning queries.
5. Update database usage docs.
6. Run focused and configured verification.

## Verification

- `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_db_query_runs_sqlite_select_and_writes`
- `python -m unittest discover -s tests`
- `python -m compileall src`
- `scripts\aiflow-dev.bat verify --auto --continue-on-error`
