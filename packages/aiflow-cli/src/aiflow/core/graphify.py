from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .markdown import now_stamp
from .memory import list_memory_entries


CONCEPT_WORDS = ["CodeGraph", "Graphify", "workflow", "Agent", "memory", "context", "review", "verify"]


def graphify_dir(root: Path) -> Path:
    return root / ".aiflow" / "graphify"


def build_graphify(root: Path, *, output_dir: Path | None = None) -> dict[str, Any]:
    output = output_dir or graphify_dir(root)
    output.mkdir(parents=True, exist_ok=True)
    generated_at = now_stamp()
    sources = project_knowledge_sources(root)
    memory = list_memory_entries(root, limit=100)
    concepts = extract_concepts(root, sources, memory)
    relations = build_relations(sources, concepts)

    knowledge_payload = {"layer": "Graphify", "generated_at": generated_at, "sources": sources, "memory": memory}
    concepts_payload = {"layer": "Graphify", "generated_at": generated_at, "concepts": concepts}
    relations_payload = {"layer": "Graphify", "generated_at": generated_at, "relations": relations}
    write_json(output / "knowledge.json", knowledge_payload)
    write_json(output / "concepts.json", concepts_payload)
    write_json(output / "relations.json", relations_payload)
    summary = render_graphify_summary(knowledge_payload, concepts_payload, relations_payload)
    (output / "summary.md").write_text(summary, encoding="utf-8", newline="\n")
    return {"knowledge": knowledge_payload, "concepts": concepts_payload, "relations": relations_payload, "summary": summary}


def project_knowledge_sources(root: Path) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    readme = root / "README.md"
    if readme.exists():
        candidates.append(readme)
    docs = root / "docs"
    if docs.exists():
        candidates.extend(sorted(docs.rglob("*.md")))
    sources: list[dict[str, Any]] = []
    for path in candidates:
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        headings = [line.lstrip("#").strip() for line in text.splitlines() if line.startswith("#")]
        sources.append({"path": relative, "title": headings[0] if headings else path.stem, "headings": headings[:20]})
    return sources


def extract_concepts(root: Path, sources: list[dict[str, Any]], memory: list[str]) -> list[dict[str, Any]]:
    text_parts: list[str] = []
    for source in sources:
        path = root / source["path"]
        text_parts.append(path.read_text(encoding="utf-8", errors="replace"))
    text_parts.extend(memory)
    corpus = "\n".join(text_parts)
    concepts: list[dict[str, Any]] = []
    for word in CONCEPT_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", corpus, flags=re.IGNORECASE):
            concepts.append({"id": slug(word), "name": word})
    return concepts


def build_relations(sources: list[dict[str, Any]], concepts: list[dict[str, Any]]) -> list[dict[str, str]]:
    relations: list[dict[str, str]] = []
    for source in sources:
        source_id = f"source:{source['path']}"
        for concept in concepts:
            relations.append({"from": source_id, "to": f"concept:{concept['id']}", "type": "documents"})
    return relations


def render_graphify_summary(knowledge_payload: dict[str, Any], concepts_payload: dict[str, Any], relations_payload: dict[str, Any]) -> str:
    return f"""# Graphify

Graphify is the project knowledge layer.

- Sources: {len(knowledge_payload["sources"])}
- Memory entries: {len(knowledge_payload["memory"])}
- Concepts: {len(concepts_payload["concepts"])}
- Relations: {len(relations_payload["relations"])}
"""


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
