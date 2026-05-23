from __future__ import annotations


RISK_KEYWORDS = ["auth", "security", "payment", "secret", "token", "password", "migration", "database"]
TEST_MARKERS = ["test", "tests", "spec", "__tests__"]


def risk_signals(changed_files: list[str], high_risk_paths: list[str]) -> list[str]:
    signals: list[str] = []
    for path in changed_files:
        normalized = path.replace("\\", "/").lower()
        if any(normalized.startswith(prefix.lower().replace("\\", "/")) for prefix in high_risk_paths):
            signals.append(f"High risk path changed: `{path}`")
        if any(keyword in normalized for keyword in RISK_KEYWORDS):
            signals.append(f"Risk keyword in changed path: `{path}`")
        if normalized.endswith((".lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock")):
            signals.append(f"Lockfile changed: `{path}`")
    if changed_files and not any(any(marker in path.lower() for marker in TEST_MARKERS) for path in changed_files):
        signals.append("Changed files do not include obvious tests.")
    return sorted(set(signals))
