from __future__ import annotations

import sqlite3
import tomllib
import json
from dataclasses import dataclass
from importlib.util import find_spec
from os import environ
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


DATABASE_TYPES = ["sqlite", "mysql", "postgres", "sqlserver", "oracle", "mongodb"]

DRIVER_HELP = {
    "mysql": "Install a project-local driver, for example: python -m pip install PyMySQL",
    "postgres": "Install a project-local driver, for example: python -m pip install psycopg[binary]",
    "sqlserver": "Install a project-local driver, for example: python -m pip install pyodbc or pymssql. pyodbc also needs a system ODBC driver.",
    "oracle": "Install a project-local driver, for example: python -m pip install oracledb",
    "mongodb": "Install a project-local driver, for example: python -m pip install pymongo",
}


@dataclass
class DatabaseResult:
    ok: bool
    message: str
    rows: list[Any] | None = None
    columns: list[str] | None = None


def database_config_path(root: Path) -> Path:
    return root / ".aiflow" / "databases.toml"


def database_local_path(root: Path) -> Path:
    return root / ".aiflow" / "databases.local.toml"


def load_database_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"databases": {}}
    with path.open("rb") as f:
        data = tomllib.load(f)
    data.setdefault("databases", {})
    return data


def load_databases(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return load_database_file(database_config_path(root)), load_database_file(database_local_path(root))


def save_database_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_toml(data), encoding="utf-8", newline="\n")


def dumps_toml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    databases = data.get("databases", {})
    for name in sorted(databases):
        lines.append(f"[databases.{name}]")
        for key, value in databases[name].items():
            if value is None or value == "":
                continue
            lines.append(f"{key} = {format_toml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def redact_profile(name: str, config_profile: dict[str, Any], local_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    local_profile = local_profile or {}
    result = {"name": name, **config_profile}
    for key in ["dsn", "user", "password"]:
        if key in local_profile:
            result[f"{key}_local"] = "***"
    return result


def resolve_database_profile(root: Path, name: str) -> dict[str, Any] | None:
    config, local = load_databases(root)
    config_profile = config.get("databases", {}).get(name)
    if not config_profile:
        return None

    profile = dict(config_profile)
    local_profile = local.get("databases", {}).get(name, {})
    profile.update(local_profile)

    for value_key, env_key in [("dsn", "dsn_env"), ("user", "user_env"), ("password", "password_env")]:
        env_name = profile.get(env_key)
        if env_name and environ.get(str(env_name)):
            profile[value_key] = environ[str(env_name)]
    return profile


def sqlite_test(path: Path) -> tuple[bool, str]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.execute("select 1")
        conn.close()
        return True, f"sqlite ok: {path}"
    except Exception as exc:
        return False, f"sqlite failed: {exc}"


def test_database_profile(root: Path, profile: dict[str, Any]) -> DatabaseResult:
    db_type = profile.get("type")
    if db_type == "sqlite":
        db_path = sqlite_path(root, profile)
        ok, message = sqlite_test(db_path)
        return DatabaseResult(ok, message)
    if db_type == "mysql":
        return _test_mysql(profile)
    if db_type == "postgres":
        return _test_postgres(profile)
    if db_type == "sqlserver":
        return _test_sqlserver(profile)
    if db_type == "oracle":
        return _test_oracle(profile)
    if db_type == "mongodb":
        return _test_mongodb(profile)
    return DatabaseResult(False, f"Unsupported database type: {db_type}")


def list_database_tables(root: Path, profile: dict[str, Any], schema: str = "") -> DatabaseResult:
    db_type = profile.get("type")
    if db_type == "sqlite":
        db_path = sqlite_path(root, profile)
        return _sqlite_tables(db_path)
    if db_type == "mysql":
        return _mysql_tables(profile)
    if db_type == "postgres":
        return _postgres_tables(profile, schema)
    if db_type == "sqlserver":
        return _sqlserver_tables(profile, schema)
    if db_type == "oracle":
        return _oracle_tables(profile, schema)
    if db_type == "mongodb":
        return _mongodb_collections(profile)
    return DatabaseResult(False, f"Unsupported database type: {db_type}")


def query_database_profile(
    root: Path,
    profile: dict[str, Any],
    query: str,
    *,
    limit: int = 100,
    mongo_collection: str = "",
    mongo_filter_json: str = "",
    mongo_projection_json: str = "",
    mongo_command_json: str = "",
) -> DatabaseResult:
    db_type = profile.get("type")
    if db_type == "sqlite":
        db_path = sqlite_path(root, profile)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return _execute_sql_query("sqlite", sqlite3.connect(db_path), query, limit)
    if db_type == "mysql":
        return _mysql_query(profile, query, limit)
    if db_type == "postgres":
        conn = _postgres_connect(profile)
        if conn is None:
            return _missing_driver("postgres", ["psycopg", "psycopg2"])
        return _execute_sql_query("postgres", conn, query, limit)
    if db_type == "sqlserver":
        try:
            conn, _driver_name = _sqlserver_connect(profile)
        except Exception as exc:
            return DatabaseResult(False, f"sqlserver query failed: {exc}")
        if conn is None:
            return _missing_driver("sqlserver", ["pyodbc", "pymssql"])
        return _execute_sql_query("sqlserver", conn, query, limit)
    if db_type == "oracle":
        conn = _oracle_connect(profile)
        if conn is None:
            return _missing_driver("oracle", ["oracledb", "cx_Oracle"])
        return _execute_sql_query("oracle", conn, query, limit)
    if db_type == "mongodb":
        return _mongodb_query(
            profile,
            query,
            limit=limit,
            collection=mongo_collection,
            filter_json=mongo_filter_json,
            projection_json=mongo_projection_json,
            command_json=mongo_command_json,
        )
    return DatabaseResult(False, f"Unsupported database type: {db_type}")


def sqlite_path(root: Path, profile: dict[str, Any]) -> Path:
    db_path = Path(profile.get("path") or profile.get("database", ""))
    if not db_path.is_absolute():
        db_path = root / db_path
    return db_path


def _sqlite_tables(path: Path) -> DatabaseResult:
    try:
        conn = sqlite3.connect(path)
        rows = conn.execute(
            "select name from sqlite_master where type = 'table' and name not like 'sqlite_%' order by name"
        ).fetchall()
        conn.close()
        tables = [row[0] for row in rows]
        return DatabaseResult(True, f"sqlite tables: {len(tables)}", tables)
    except Exception as exc:
        return DatabaseResult(False, f"sqlite table list failed: {exc}")


def _missing_driver(db_type: str, modules: list[str]) -> DatabaseResult:
    choices = ", ".join(modules)
    return DatabaseResult(False, f"{db_type} driver not found ({choices}). {DRIVER_HELP[db_type]}")


def _normalize_cell(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _execute_sql_query(db_type: str, conn: Any, query: str, limit: int) -> DatabaseResult:
    try:
        cur = conn.cursor()
        try:
            cur.execute(query)
            if cur.description:
                columns = [str(column[0]) for column in cur.description]
                fetched = cur.fetchall() if limit <= 0 else cur.fetchmany(limit)
                rows = [[_normalize_cell(value) for value in row] for row in fetched]
                return DatabaseResult(True, f"{db_type} query rows: {len(rows)}", rows, columns)
            conn.commit()
            affected = cur.rowcount if getattr(cur, "rowcount", -1) >= 0 else "unknown"
            return DatabaseResult(True, f"{db_type} query affected: {affected}")
        finally:
            cur.close()
            conn.close()
    except Exception as exc:
        return DatabaseResult(False, f"{db_type} query failed: {exc}")


def _has_module(name: str) -> bool:
    try:
        return find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def _parse_url_dsn(dsn: str) -> dict[str, Any]:
    parsed = urlparse(dsn)
    return {
        "host": parsed.hostname or "",
        "port": parsed.port or 0,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": unquote(parsed.path.lstrip("/")),
    }


def _mysql_connect_kwargs(profile: dict[str, Any]) -> dict[str, Any]:
    values = _parse_url_dsn(profile["dsn"]) if profile.get("dsn") else {}
    values = {**values, **{k: v for k, v in profile.items() if k in {"host", "port", "user", "password", "database"}}}
    return {
        "host": values.get("host") or "127.0.0.1",
        "port": int(values.get("port") or 3306),
        "user": values.get("user") or "",
        "password": values.get("password") or "",
        "database": values.get("database") or "",
        "charset": "utf8mb4",
        "connect_timeout": int(profile.get("connect_timeout") or 10),
    }


def _test_mysql(profile: dict[str, Any]) -> DatabaseResult:
    if _has_module("pymysql"):
        try:
            import pymysql

            conn = pymysql.connect(**_mysql_connect_kwargs(profile))
            with conn.cursor() as cur:
                cur.execute("select 1")
            conn.close()
            return DatabaseResult(True, "mysql ok")
        except Exception as exc:
            return DatabaseResult(False, f"mysql failed: {exc}")
    if _has_module("mysql.connector"):
        try:
            import mysql.connector

            kwargs = _mysql_connect_kwargs(profile)
            kwargs["connection_timeout"] = kwargs.pop("connect_timeout")
            conn = mysql.connector.connect(**kwargs)
            cur = conn.cursor()
            cur.execute("select 1")
            cur.close()
            conn.close()
            return DatabaseResult(True, "mysql ok")
        except Exception as exc:
            return DatabaseResult(False, f"mysql failed: {exc}")
    return _missing_driver("mysql", ["pymysql", "mysql.connector"])


def _mysql_tables(profile: dict[str, Any]) -> DatabaseResult:
    try:
        if _has_module("pymysql"):
            import pymysql

            conn = pymysql.connect(**_mysql_connect_kwargs(profile))
            with conn.cursor() as cur:
                cur.execute("show tables")
                rows = [row[0] for row in cur.fetchall()]
            conn.close()
            return DatabaseResult(True, f"mysql tables: {len(rows)}", rows)
        if _has_module("mysql.connector"):
            import mysql.connector

            kwargs = _mysql_connect_kwargs(profile)
            kwargs["connection_timeout"] = kwargs.pop("connect_timeout")
            conn = mysql.connector.connect(**kwargs)
            cur = conn.cursor()
            cur.execute("show tables")
            rows = [row[0] for row in cur.fetchall()]
            cur.close()
            conn.close()
            return DatabaseResult(True, f"mysql tables: {len(rows)}", rows)
        return _missing_driver("mysql", ["pymysql", "mysql.connector"])
    except Exception as exc:
        return DatabaseResult(False, f"mysql table list failed: {exc}")


def _mysql_query(profile: dict[str, Any], query: str, limit: int) -> DatabaseResult:
    try:
        if _has_module("pymysql"):
            import pymysql

            conn = pymysql.connect(**_mysql_connect_kwargs(profile))
            return _execute_sql_query("mysql", conn, query, limit)
        if _has_module("mysql.connector"):
            import mysql.connector

            kwargs = _mysql_connect_kwargs(profile)
            kwargs["connection_timeout"] = kwargs.pop("connect_timeout")
            conn = mysql.connector.connect(**kwargs)
            return _execute_sql_query("mysql", conn, query, limit)
        return _missing_driver("mysql", ["pymysql", "mysql.connector"])
    except Exception as exc:
        return DatabaseResult(False, f"mysql query failed: {exc}")


def _postgres_connect(profile: dict[str, Any]):
    kwargs = {
        "host": profile.get("host") or "127.0.0.1",
        "port": int(profile.get("port") or 5432),
        "dbname": profile.get("database") or "",
        "user": profile.get("user") or "",
        "password": profile.get("password") or "",
        "connect_timeout": int(profile.get("connect_timeout") or 10),
    }
    if _has_module("psycopg"):
        import psycopg

        return psycopg.connect(profile["dsn"]) if profile.get("dsn") else psycopg.connect(**kwargs)
    if _has_module("psycopg2"):
        import psycopg2

        return psycopg2.connect(profile["dsn"]) if profile.get("dsn") else psycopg2.connect(**kwargs)
    return None


def _test_postgres(profile: dict[str, Any]) -> DatabaseResult:
    try:
        conn = _postgres_connect(profile)
        if conn is None:
            return _missing_driver("postgres", ["psycopg", "psycopg2"])
        with conn.cursor() as cur:
            cur.execute("select 1")
        conn.close()
        return DatabaseResult(True, "postgres ok")
    except Exception as exc:
        return DatabaseResult(False, f"postgres failed: {exc}")


def _postgres_tables(profile: dict[str, Any], schema: str) -> DatabaseResult:
    try:
        conn = _postgres_connect(profile)
        if conn is None:
            return _missing_driver("postgres", ["psycopg", "psycopg2"])
        sql = """
            select table_schema || '.' || table_name
            from information_schema.tables
            where table_type = 'BASE TABLE'
              and table_schema not in ('pg_catalog', 'information_schema')
        """
        params: list[str] = []
        if schema:
            sql += " and table_schema = %s"
            params.append(schema)
        sql += " order by table_schema, table_name"
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = [row[0] for row in cur.fetchall()]
        conn.close()
        return DatabaseResult(True, f"postgres tables: {len(rows)}", rows)
    except Exception as exc:
        return DatabaseResult(False, f"postgres table list failed: {exc}")


def _sqlserver_pyodbc_connect(profile: dict[str, Any]):
    import pyodbc

    if profile.get("dsn"):
        return pyodbc.connect(profile["dsn"], timeout=int(profile.get("connect_timeout") or 10))
    driver = profile.get("driver") or "ODBC Driver 18 for SQL Server"
    server = profile.get("host") or "127.0.0.1"
    if profile.get("port"):
        server = f"{server},{int(profile['port'])}"
    database = profile.get("database") or ""
    user = profile.get("user") or ""
    password = profile.get("password") or ""
    connection = (
        f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={password};"
        "TrustServerCertificate=yes"
    )
    return pyodbc.connect(connection, timeout=int(profile.get("connect_timeout") or 10))


def _sqlserver_pymssql_connect(profile: dict[str, Any]):
    import pymssql

    return pymssql.connect(
        server=profile.get("host") or "127.0.0.1",
        port=int(profile.get("port") or 1433),
        user=profile.get("user") or "",
        password=profile.get("password") or "",
        database=profile.get("database") or "",
        login_timeout=int(profile.get("connect_timeout") or 10),
        timeout=int(profile.get("query_timeout") or 30),
    )


def _sqlserver_connect(profile: dict[str, Any]):
    errors: list[str] = []
    if _has_module("pyodbc"):
        try:
            return _sqlserver_pyodbc_connect(profile), "pyodbc"
        except Exception as exc:
            errors.append(f"pyodbc: {exc}")
    if _has_module("pymssql"):
        try:
            return _sqlserver_pymssql_connect(profile), "pymssql"
        except Exception as exc:
            errors.append(f"pymssql: {exc}")
    if errors:
        raise RuntimeError("; ".join(errors))
    return None, ""


def _test_sqlserver(profile: dict[str, Any]) -> DatabaseResult:
    try:
        conn, _driver_name = _sqlserver_connect(profile)
        if conn is None:
            return _missing_driver("sqlserver", ["pyodbc", "pymssql"])
        cur = conn.cursor()
        cur.execute("select 1")
        cur.close()
        conn.close()
        return DatabaseResult(True, "sqlserver ok")
    except Exception as exc:
        return DatabaseResult(False, f"sqlserver failed: {exc}")


def _sqlserver_tables(profile: dict[str, Any], schema: str) -> DatabaseResult:
    try:
        conn, driver_name = _sqlserver_connect(profile)
        if conn is None:
            return _missing_driver("sqlserver", ["pyodbc", "pymssql"])
        sql = """
            select table_schema + '.' + table_name
            from information_schema.tables
            where table_type = 'BASE TABLE'
        """
        params: list[str] = []
        if schema:
            sql += " and table_schema = ?" if driver_name == "pyodbc" else " and table_schema = %s"
            params.append(schema)
        sql += " order by table_schema, table_name"
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return DatabaseResult(True, f"sqlserver tables: {len(rows)}", rows)
    except Exception as exc:
        return DatabaseResult(False, f"sqlserver table list failed: {exc}")


def _oracle_connect(profile: dict[str, Any]):
    module = None
    if _has_module("oracledb"):
        import oracledb

        module = oracledb
    elif _has_module("cx_Oracle"):
        import cx_Oracle

        module = cx_Oracle
    if module is None:
        return None
    if profile.get("dsn"):
        dsn = profile["dsn"]
    else:
        dsn = module.makedsn(
            profile.get("host") or "127.0.0.1",
            int(profile.get("port") or 1521),
            service_name=profile.get("database") or "",
        )
    return module.connect(user=profile.get("user") or "", password=profile.get("password") or "", dsn=dsn)


def _test_oracle(profile: dict[str, Any]) -> DatabaseResult:
    try:
        conn = _oracle_connect(profile)
        if conn is None:
            return _missing_driver("oracle", ["oracledb", "cx_Oracle"])
        with conn.cursor() as cur:
            cur.execute("select 1 from dual")
        conn.close()
        return DatabaseResult(True, "oracle ok")
    except Exception as exc:
        return DatabaseResult(False, f"oracle failed: {exc}")


def _oracle_tables(profile: dict[str, Any], schema: str) -> DatabaseResult:
    try:
        conn = _oracle_connect(profile)
        if conn is None:
            return _missing_driver("oracle", ["oracledb", "cx_Oracle"])
        owner = (schema or profile.get("schema") or "").upper()
        sql = "select table_name from all_tables"
        params: list[str] = []
        if owner:
            sql += " where owner = :1"
            params.append(owner)
        sql += " order by owner, table_name"
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = [row[0] for row in cur.fetchall()]
        conn.close()
        return DatabaseResult(True, f"oracle tables: {len(rows)}", rows)
    except Exception as exc:
        return DatabaseResult(False, f"oracle table list failed: {exc}")


def _mongodb_client(profile: dict[str, Any]):
    if not _has_module("pymongo"):
        return None
    from pymongo import MongoClient

    if profile.get("dsn"):
        return MongoClient(profile["dsn"], serverSelectionTimeoutMS=int(profile.get("connect_timeout") or 10) * 1000)
    kwargs: dict[str, Any] = {
        "host": profile.get("host") or "127.0.0.1",
        "port": int(profile.get("port") or 27017),
        "serverSelectionTimeoutMS": int(profile.get("connect_timeout") or 10) * 1000,
    }
    if profile.get("user"):
        kwargs["username"] = profile.get("user")
    if profile.get("password"):
        kwargs["password"] = profile.get("password")
    return MongoClient(**kwargs)


def _test_mongodb(profile: dict[str, Any]) -> DatabaseResult:
    try:
        client = _mongodb_client(profile)
        if client is None:
            return _missing_driver("mongodb", ["pymongo"])
        client.admin.command("ping")
        client.close()
        return DatabaseResult(True, "mongodb ok")
    except Exception as exc:
        return DatabaseResult(False, f"mongodb failed: {exc}")


def _mongodb_collections(profile: dict[str, Any]) -> DatabaseResult:
    try:
        client = _mongodb_client(profile)
        if client is None:
            return _missing_driver("mongodb", ["pymongo"])
        database = profile.get("database")
        if database:
            rows = sorted(client[database].list_collection_names())
            message = f"mongodb collections: {len(rows)}"
        else:
            rows = sorted(client.list_database_names())
            message = f"mongodb databases: {len(rows)}"
        client.close()
        return DatabaseResult(True, message, rows)
    except Exception as exc:
        return DatabaseResult(False, f"mongodb collection list failed: {exc}")


def _parse_json_object(raw: str, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if not raw:
        return fallback or {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


def _mongodb_query(
    profile: dict[str, Any],
    query: str,
    *,
    limit: int,
    collection: str,
    filter_json: str,
    projection_json: str,
    command_json: str,
) -> DatabaseResult:
    try:
        client = _mongodb_client(profile)
        if client is None:
            return _missing_driver("mongodb", ["pymongo"])
        database_name = profile.get("database")
        if not database_name:
            client.close()
            return DatabaseResult(False, "mongodb query requires a configured database")
        database = client[database_name]
        if command_json:
            result = database.command(_parse_json_object(command_json))
            client.close()
            return DatabaseResult(True, "mongodb command result: 1", [result])
        if not collection:
            client.close()
            return DatabaseResult(False, "mongodb query requires --collection or --command-json")
        filter_value = _parse_json_object(filter_json or query, {})
        projection = _parse_json_object(projection_json) if projection_json else None
        cursor = database[collection].find(filter_value, projection)
        if limit > 0:
            cursor = cursor.limit(limit)
        rows = [{key: _normalize_cell(value) for key, value in row.items()} for row in cursor]
        client.close()
        return DatabaseResult(True, f"mongodb query rows: {len(rows)}", rows)
    except Exception as exc:
        return DatabaseResult(False, f"mongodb query failed: {exc}")
