from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from os import environ
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


@dataclass
class NacosResult:
    ok: bool
    message: str
    content: str = ""
    status: int = 0


def nacos_config_path(root: Path) -> Path:
    return root / ".aiflow" / "nacos.toml"


def nacos_local_path(root: Path) -> Path:
    return root / ".aiflow" / "nacos.local.toml"


def load_nacos_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"nacos": {}}
    with path.open("rb") as f:
        data = tomllib.load(f)
    data.setdefault("nacos", {})
    return data


def load_nacos(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return load_nacos_file(nacos_config_path(root)), load_nacos_file(nacos_local_path(root))


def save_nacos_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_toml(data), encoding="utf-8", newline="\n")


def dumps_toml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    profiles = data.get("nacos", {})
    for name in sorted(profiles):
        lines.append(f"[nacos.{name}]")
        for key, value in profiles[name].items():
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
    for key in ["username", "password", "access_token"]:
        if key in local_profile:
            result[f"{key}_local"] = "***"
    return result


def resolve_nacos_profile(root: Path, name: str) -> dict[str, Any] | None:
    config, local = load_nacos(root)
    config_profile = config.get("nacos", {}).get(name)
    if not config_profile:
        return None

    profile = dict(config_profile)
    profile.update(local.get("nacos", {}).get(name, {}))
    for value_key, env_key in [
        ("username", "username_env"),
        ("password", "password_env"),
        ("access_token", "access_token_env"),
    ]:
        env_name = profile.get(env_key)
        if env_name and environ.get(str(env_name)):
            profile[value_key] = environ[str(env_name)]
    return profile


def fetch_nacos_config(
    profile: dict[str, Any],
    *,
    data_id: str,
    group: str,
    namespace: str = "",
    timeout: int = 10,
) -> NacosResult:
    if not data_id:
        return NacosResult(False, "nacos get requires --data-id")
    if not group:
        return NacosResult(False, "nacos get requires --group")

    try:
        token = profile.get("access_token") or _login_for_token(profile, timeout)
        params = {"dataId": data_id, "group": group}
        tenant = namespace or profile.get("namespace") or ""
        if tenant:
            params["tenant"] = tenant
        if token:
            params["accessToken"] = str(token)
        url = _api_url(profile, "/nacos/v1/cs/configs") + "?" + urlencode(params)
        request = Request(url, headers={"Accept": "text/plain, */*"})
        with urlopen(request, timeout=timeout) as response:
            content = response.read().decode(_response_charset(response.headers.get("Content-Type")))
            status = int(getattr(response, "status", 200))
        return NacosResult(True, f"nacos config fetched: {data_id}", content, status)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return NacosResult(False, f"nacos fetch failed: HTTP {exc.code} {body}".strip(), status=exc.code)
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return NacosResult(False, f"nacos fetch failed: {exc}")


def _login_for_token(profile: dict[str, Any], timeout: int) -> str:
    username = profile.get("username")
    password = profile.get("password")
    if not username or not password:
        return ""
    payload = urlencode({"username": username, "password": password}).encode("utf-8")
    request = Request(
        _api_url(profile, "/nacos/v1/auth/login"),
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode(_response_charset(response.headers.get("Content-Type")))
    data = json.loads(raw)
    return str(data.get("accessToken") or "")


def _api_url(profile: dict[str, Any], path: str) -> str:
    server = profile.get("server") or _server_from_host_port(profile)
    if not server:
        raise ValueError("nacos profile requires server or host/port")
    return urljoin(str(server).rstrip("/") + "/", path.lstrip("/"))


def _server_from_host_port(profile: dict[str, Any]) -> str:
    host = profile.get("host")
    if not host:
        return ""
    scheme = profile.get("scheme") or "http"
    port = int(profile.get("port") or 8848)
    return f"{scheme}://{host}:{port}"


def _response_charset(content_type: str | None) -> str:
    if content_type:
        for part in content_type.split(";"):
            part = part.strip()
            if part.lower().startswith("charset="):
                return part.split("=", 1)[1] or "utf-8"
    return "utf-8"
