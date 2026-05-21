from __future__ import annotations

import json
import secrets
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from typing import Any

from .config import load_config
from .markdown import now_stamp


CAPTURE_TYPES = {"page", "selection"}
AUTOMATION_ACTIONS = {"extract", "click", "fill", "wait", "open"}
EXTENSION_ORIGIN_PREFIXES = ("chrome-extension://", "edge-extension://")
SENSITIVE_QUERY_KEYS = {"token", "access_token", "auth", "authorization", "key", "api_key", "secret", "password", "session", "jwt"}


class CaptureError(ValueError):
    pass


def browser_config(root: Path) -> dict[str, Any]:
    return load_config(root).get("browser", {})


def resolve_project_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def capture_dir(root: Path, config: dict[str, Any] | None = None) -> Path:
    current = config or browser_config(root)
    return resolve_project_path(root, str(current.get("capture_dir", ".aiflow/browser/captures")))


def elements_dir(root: Path, config: dict[str, Any] | None = None) -> Path:
    current = config or browser_config(root)
    return resolve_project_path(root, str(current.get("elements_dir", ".aiflow/browser/elements")))


def pages_dir(root: Path, config: dict[str, Any] | None = None) -> Path:
    current = config or browser_config(root)
    return resolve_project_path(root, str(current.get("pages_dir", ".aiflow/browser/pages")))


def requests_dir(root: Path, config: dict[str, Any] | None = None) -> Path:
    current = config or browser_config(root)
    return resolve_project_path(root, str(current.get("requests_dir", ".aiflow/browser/requests")))


def actions_dir(root: Path, config: dict[str, Any] | None = None) -> Path:
    current = config or browser_config(root)
    return resolve_project_path(root, str(current.get("actions_dir", ".aiflow/browser/actions")))


def pending_actions_dir(root: Path, config: dict[str, Any] | None = None) -> Path:
    return actions_dir(root, config) / "pending"


def completed_actions_dir(root: Path, config: dict[str, Any] | None = None) -> Path:
    return actions_dir(root, config) / "completed"


def token_path(root: Path, config: dict[str, Any] | None = None) -> Path:
    current = config or browser_config(root)
    return resolve_project_path(root, str(current.get("token_file", ".aiflow/browser/token")))


def ensure_browser_token(root: Path, config: dict[str, Any] | None = None) -> str:
    path = token_path(root, config)
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token
    path.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(24)
    path.write_text(token + "\n", encoding="utf-8", newline="\n")
    return token


def read_browser_token(root: Path, config: dict[str, Any] | None = None) -> str | None:
    path = token_path(root, config)
    if not path.exists():
        return None
    token = path.read_text(encoding="utf-8").strip()
    return token or None


def write_capture(root: Path, payload: dict[str, Any], config: dict[str, Any] | None = None) -> Path:
    normalized = normalize_capture(payload)
    output_dir = capture_dir(root, config)
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    path = unique_capture_path(output_dir, stamp, normalized["type"])
    path.write_text(render_capture(normalized), encoding="utf-8", newline="\n")
    return path


def write_element_capture(root: Path, payload: dict[str, Any], config: dict[str, Any] | None = None) -> Path:
    normalized = normalize_element_capture(payload)
    output_dir = elements_dir(root, config)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    path = unique_json_path(output_dir, stamp, "element")
    write_json_file(path, normalized)
    return path


def write_page_snapshot(root: Path, payload: dict[str, Any], config: dict[str, Any] | None = None) -> Path:
    normalized = normalize_page_snapshot(payload)
    output_dir = pages_dir(root, config)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    path = unique_json_path(output_dir, stamp, "page")
    write_json_file(path, normalized)
    return path


def write_request_capture(root: Path, payload: dict[str, Any], config: dict[str, Any] | None = None) -> Path:
    normalized = normalize_request_capture(payload)
    output_dir = requests_dir(root, config)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    path = unique_json_path(output_dir, stamp, "requests")
    write_json_file(path, normalized)
    return path


def write_automation_job(
    root: Path,
    steps: list[dict[str, str]],
    *,
    note: str = "",
    config: dict[str, Any] | None = None,
) -> Path:
    normalized_steps = normalize_automation_steps(steps)
    current = config or browser_config(root)
    output_dir = pending_actions_dir(root, current)
    output_dir.mkdir(parents=True, exist_ok=True)
    job_id = unique_action_id(output_dir)
    payload = {
        "id": job_id,
        "created_at": now_stamp(),
        "note": clean_text(note, max_chars=2_000),
        "steps": normalized_steps,
    }
    path = output_dir / f"{job_id}.json"
    write_json_file(path, payload)
    return path


def next_automation_job(root: Path, config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    current = config or browser_config(root)
    pending = pending_actions_dir(root, current)
    if not pending.exists():
        return None
    for path in sorted(pending.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("id"), str):
            return payload
    return None


def complete_automation_job(
    root: Path,
    job_id: str,
    result: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> Path:
    safe_id = clean_action_id(job_id)
    current = config or browser_config(root)
    pending = pending_actions_dir(root, current) / f"{safe_id}.json"
    if not pending.exists():
        raise CaptureError(f"automation job not found: {safe_id}")
    job = json.loads(pending.read_text(encoding="utf-8"))
    status = clean_text(result.get("status", "completed"), max_chars=40).lower() or "completed"
    if status not in {"completed", "failed"}:
        raise CaptureError("automation result status must be completed or failed")
    output = {
        "id": safe_id,
        "completed_at": now_stamp(),
        "status": status,
        "job": job,
        "result": limit_json(result, max_chars=120_000),
    }
    done_dir = completed_actions_dir(root, current)
    done_dir.mkdir(parents=True, exist_ok=True)
    output_path = done_dir / f"{safe_id}.json"
    write_json_file(output_path, output)
    pending.unlink()
    return output_path


def normalize_automation_steps(steps: list[dict[str, str]]) -> list[dict[str, str]]:
    if not steps:
        raise CaptureError("automation job requires at least one step")
    if len(steps) > 50:
        raise CaptureError("automation job can contain at most 50 steps")

    normalized: list[dict[str, str]] = []
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise CaptureError(f"automation step {index} must be an object")
        action = clean_text(step.get("action", ""), max_chars=40).lower()
        if action not in AUTOMATION_ACTIONS:
            raise CaptureError(f"unsupported automation action: {action}")
        selector = clean_text(step.get("selector", ""), max_chars=1_000)
        value = clean_text(step.get("value", ""), max_chars=20_000)
        if action in {"click", "fill"} and not selector:
            raise CaptureError(f"automation action {action} requires a selector")
        if action == "open":
            target_url = value or selector
            if not is_allowed_browser_url(target_url):
                raise CaptureError("open step requires an http or https URL")
            selector = ""
            value = target_url
        if action == "wait":
            try:
                delay = int(value or selector or "1000")
            except ValueError as exc:
                raise CaptureError("wait step value must be milliseconds") from exc
            if delay < 0 or delay > 60_000:
                raise CaptureError("wait step must be between 0 and 60000 milliseconds")
            value = str(delay)
            selector = ""
        normalized.append({"action": action, "selector": selector, "value": value})
    return normalized


def is_allowed_browser_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_capture(payload: dict[str, Any]) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise CaptureError("capture payload must be an object")

    capture_type = clean_text(payload.get("type", "selection"), max_chars=40).lower() or "selection"
    if capture_type not in CAPTURE_TYPES:
        raise CaptureError(f"unsupported capture type: {capture_type}")

    url = clean_text(payload.get("url", ""), max_chars=2_048)
    title = clean_text(payload.get("title", ""), max_chars=500)
    selection = clean_text(payload.get("selection", ""), max_chars=120_000)
    note = clean_text(payload.get("note", ""), max_chars=40_000)
    if not any([url, title, selection, note]):
        raise CaptureError("capture payload is empty")

    return {
        "type": capture_type,
        "url": url,
        "title": title,
        "selection": selection,
        "note": note,
    }


def normalize_element_capture(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CaptureError("element payload must be an object")

    tag_name = clean_text(payload.get("tagName", ""), max_chars=80).lower()
    selector = clean_text(payload.get("selector", ""), max_chars=2_000)
    if not tag_name or not selector:
        raise CaptureError("element payload requires tagName and selector")

    attributes = normalize_scalar_map(payload.get("attributes", {}), max_items=50, max_chars=500)
    input_type = attributes.get("type", "").lower()
    raw_value = "" if input_type in {"password", "hidden"} else clean_text(payload.get("value", ""), max_chars=2_000)

    return {
        "captured_at": now_stamp(),
        "url": clean_text(payload.get("url", ""), max_chars=2_048),
        "title": clean_text(payload.get("title", ""), max_chars=500),
        "selector": selector,
        "tagName": tag_name,
        "id": clean_text(payload.get("id", ""), max_chars=300),
        "className": clean_text(payload.get("className", ""), max_chars=1_000),
        "text": clean_text(payload.get("text", ""), max_chars=2_000),
        "href": clean_text(payload.get("href", ""), max_chars=2_048),
        "value": raw_value,
        "attributes": attributes,
        "rect": normalize_rect(payload.get("rect", {})),
    }


def normalize_page_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CaptureError("page payload must be an object")
    url = clean_text(payload.get("url", ""), max_chars=2_048)
    title = clean_text(payload.get("title", ""), max_chars=500)
    html = clean_text(payload.get("html", ""), max_chars=500_000)
    text = clean_text(payload.get("text", ""), max_chars=120_000)
    if not any([url, title, html, text]):
        raise CaptureError("page payload is empty")
    return {
        "captured_at": now_stamp(),
        "url": redact_url(url),
        "title": title,
        "html": html,
        "text": text,
    }


def normalize_request_capture(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CaptureError("request payload must be an object")
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        raise CaptureError("request entries must be a list")
    normalized_entries = [normalize_request_entry(entry) for entry in entries[:500]]
    return {
        "captured_at": now_stamp(),
        "url": redact_url(clean_text(payload.get("url", ""), max_chars=2_048)),
        "title": clean_text(payload.get("title", ""), max_chars=500),
        "entries": normalized_entries,
    }


def normalize_request_entry(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise CaptureError("request entries must be objects")
    return {
        "url": redact_url(clean_text(entry.get("url", ""), max_chars=4_096)),
        "method": clean_text(entry.get("method", ""), max_chars=20).upper(),
        "status": clean_int(entry.get("status"), default=0, minimum=0, maximum=999),
        "statusText": clean_text(entry.get("statusText", ""), max_chars=200),
        "mimeType": clean_text(entry.get("mimeType", ""), max_chars=200),
        "resourceType": clean_text(entry.get("resourceType", ""), max_chars=80),
        "startedDateTime": clean_text(entry.get("startedDateTime", ""), max_chars=80),
        "time": clean_number(entry.get("time"), default=0, minimum=0, maximum=3_600_000),
    }


def redact_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlparse(value)
    query = []
    for key, item in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if any(secret in lowered for secret in SENSITIVE_QUERY_KEYS):
            query.append((key, "[REDACTED]"))
        else:
            query.append((key, item[:500]))
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def clean_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise CaptureError("integer fields must be numbers")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise CaptureError("integer fields must be numbers") from exc
    return max(minimum, min(maximum, number))


def clean_number(value: Any, *, default: float, minimum: float, maximum: float) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        raise CaptureError("number fields must be numbers")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise CaptureError("number fields must be numbers") from exc
    return max(minimum, min(maximum, number))


def normalize_scalar_map(value: Any, *, max_items: int, max_chars: int) -> dict[str, str]:
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        raise CaptureError("element attributes must be an object")
    result: dict[str, str] = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= max_items:
            break
        name = clean_text(key, max_chars=120)
        if not name:
            continue
        result[name] = clean_text(item, max_chars=max_chars)
    return result


def normalize_rect(value: Any) -> dict[str, int | float]:
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        raise CaptureError("element rect must be an object")
    rect: dict[str, int | float] = {}
    for key in ["x", "y", "width", "height"]:
        item = value.get(key)
        if item is None:
            continue
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise CaptureError("element rect values must be numbers")
        rect[key] = item
    return rect


def clean_text(value: Any, *, max_chars: int) -> str:
    if value is None:
        return ""
    if not isinstance(value, (str, int, float, bool)):
        raise CaptureError("capture fields must be scalar values")
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    return text[:max_chars]


def unique_capture_path(output_dir: Path, stamp: str, capture_type: str) -> Path:
    base = output_dir / f"{stamp}-{capture_type}.md"
    if not base.exists():
        return base
    for suffix in range(2, 10_000):
        candidate = output_dir / f"{stamp}-{capture_type}-{suffix}.md"
        if not candidate.exists():
            return candidate
    raise CaptureError("unable to allocate capture filename")


def unique_json_path(output_dir: Path, stamp: str, label: str) -> Path:
    base = output_dir / f"{stamp}-{label}.json"
    if not base.exists():
        return base
    for suffix in range(2, 10_000):
        candidate = output_dir / f"{stamp}-{label}-{suffix}.json"
        if not candidate.exists():
            return candidate
    raise CaptureError("unable to allocate JSON filename")


def unique_action_id(output_dir: Path) -> str:
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    for suffix in ["", *[f"-{index}" for index in range(2, 10_000)]]:
        candidate = f"{stamp}-automation{suffix}"
        if not (output_dir / f"{candidate}.json").exists():
            return candidate
    raise CaptureError("unable to allocate automation job id")


def clean_action_id(value: str) -> str:
    cleaned = "".join(ch for ch in value if ch.isalnum() or ch in {"-", "_"}).strip("-_")
    if not cleaned:
        raise CaptureError("invalid automation job id")
    return cleaned


def limit_json(value: Any, *, max_chars: int) -> Any:
    text = json.dumps(value, ensure_ascii=False)
    if len(text) <= max_chars:
        return value
    return {"truncated": True, "text": text[:max_chars]}


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def render_capture(capture: dict[str, str]) -> str:
    lines = [
        "# Browser Capture",
        "",
        "## Metadata",
        "",
        f"- Type: {capture['type']}",
        f"- Captured At: {now_stamp()}",
        f"- Source URL: {capture['url'] or 'Not provided'}",
        f"- Page Title: {capture['title'] or 'Not provided'}",
        "",
        "## User Note",
        "",
        capture["note"] or "Not provided.",
        "",
        "## Selection",
        "",
        capture["selection"] or "Not provided.",
        "",
    ]
    return "\n".join(lines)


class BrowserBridgeServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, root: Path, host: str, port: int, config: dict[str, Any], token: str) -> None:
        super().__init__((host, port), BrowserBridgeHandler)
        self.root = root
        self.config = config
        self.token = token


class BrowserBridgeHandler(BaseHTTPRequestHandler):
    server: BrowserBridgeServer

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.write_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "project": self.server.root.name,
                    "captureDir": display_path(self.server.root, capture_dir(self.server.root, self.server.config)),
                    "elementsDir": display_path(self.server.root, elements_dir(self.server.root, self.server.config)),
                    "pagesDir": display_path(self.server.root, pages_dir(self.server.root, self.server.config)),
                    "requestsDir": display_path(self.server.root, requests_dir(self.server.root, self.server.config)),
                    "actionsDir": display_path(self.server.root, actions_dir(self.server.root, self.server.config)),
                },
            )
            return
        if parsed.path == "/automation/next":
            if not self.has_valid_token():
                self.write_error(HTTPStatus.UNAUTHORIZED, "invalid browser token")
                return
            self.write_json(HTTPStatus.OK, {"job": next_automation_job(self.server.root, self.server.config)})
            return
        else:
            self.write_error(HTTPStatus.NOT_FOUND, "not found")
            return

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if not self.has_valid_token():
            self.write_error(HTTPStatus.UNAUTHORIZED, "invalid browser token")
            return
        if parsed.path == "/captures":
            try:
                payload = self.read_payload()
                path = write_capture(self.server.root, payload, self.server.config)
            except CaptureError as exc:
                self.write_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except json.JSONDecodeError:
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid JSON payload")
                return
            self.write_json(HTTPStatus.CREATED, {"capture": display_path(self.server.root, path)})
            return
        if parsed.path == "/elements":
            try:
                payload = self.read_payload()
                path = write_element_capture(self.server.root, payload, self.server.config)
            except CaptureError as exc:
                self.write_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except json.JSONDecodeError:
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid JSON payload")
                return
            self.write_json(HTTPStatus.CREATED, {"element": display_path(self.server.root, path)})
            return
        if parsed.path == "/pages":
            try:
                payload = self.read_payload()
                path = write_page_snapshot(self.server.root, payload, self.server.config)
            except CaptureError as exc:
                self.write_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except json.JSONDecodeError:
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid JSON payload")
                return
            self.write_json(HTTPStatus.CREATED, {"page": display_path(self.server.root, path)})
            return
        if parsed.path == "/requests":
            try:
                payload = self.read_payload()
                path = write_request_capture(self.server.root, payload, self.server.config)
            except CaptureError as exc:
                self.write_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except json.JSONDecodeError:
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid JSON payload")
                return
            self.write_json(HTTPStatus.CREATED, {"requests": display_path(self.server.root, path)})
            return
        if parsed.path.startswith("/automation/") and parsed.path.endswith("/result"):
            parts = parsed.path.strip("/").split("/")
            if len(parts) != 3:
                self.write_error(HTTPStatus.NOT_FOUND, "not found")
                return
            try:
                payload = self.read_payload()
                path = complete_automation_job(self.server.root, parts[1], payload, self.server.config)
            except CaptureError as exc:
                self.write_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except json.JSONDecodeError:
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid JSON payload")
                return
            self.write_json(HTTPStatus.CREATED, {"result": display_path(self.server.root, path)})
            return
        self.write_error(HTTPStatus.NOT_FOUND, "not found")

    def do_OPTIONS(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path not in {"/health", "/captures", "/elements", "/pages", "/requests", "/automation/next"} and not (
            parsed.path.startswith("/automation/") and parsed.path.endswith("/result")
        ):
            self.write_error(HTTPStatus.NOT_FOUND, "not found")
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.write_cors_headers()
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Aiflow-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        print(f"browser bridge: {self.address_string()} - {format % args}")

    def read_payload(self) -> dict[str, Any]:
        length = self.headers.get("Content-Length")
        if not length:
            raise CaptureError("missing content length")
        try:
            size = int(length)
        except ValueError as exc:
            raise CaptureError("invalid content length") from exc
        limit = int(self.server.config.get("max_payload_bytes", 200_000))
        if size > limit:
            raise CaptureError(f"payload exceeds {limit} bytes")
        raw = self.rfile.read(size)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise CaptureError("capture payload must be an object")
        return payload

    def has_valid_token(self) -> bool:
        return self.headers.get("X-Aiflow-Token", "") == self.server.token

    def write_error(self, status: HTTPStatus, message: str) -> None:
        self.write_json(status, {"error": message})

    def write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.write_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def write_cors_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin.startswith(EXTENSION_ORIGIN_PREFIXES):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
