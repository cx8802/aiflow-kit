# Plan

Move browser automation execution into the extension background worker and keep all target page actions backend-queued.

## Goal

- Let the project backend enqueue browser operations such as open, click, fill, scroll, wait, and extract.
- Keep the extension UI limited to bridge connection and "run next backend task".
- Execute page operations from the extension background worker through `chrome.tabs` and `chrome.scripting`.

## Non-goals

- Do not add manual URL, selector, or action input boxes to the extension UI.
- Do not let the extension execute shell commands or mutate repository files directly.
- Do not capture cookies, storage, request bodies, response bodies, or raw credentials.

## Impact Scope

- `src/aiflow/core/browser.py`
- `src/aiflow/commands/browser.py`
- `extensions/browser/background.js`
- `extensions/browser/settings.js`
- `extensions/browser/adapter-runtime.js`
- `extensions/browser/adapters/generic-page.json`
- `extensions/browser/README.md`
- `docs/23-浏览器伴随插件.md`
- `tests/test_cli_smoke.py`

## Steps

1. Done: Confirm current queue model and identify missing background execution plus scroll support.
2. Done: Add `scroll` as a normalized backend automation action and update CLI help/tests.
3. Done: Move options-page automation execution into `background.js` via `chrome.runtime.sendMessage`.
4. Done: Add scroll handling to the injected page adapter.
5. Done: Update extension docs and package metadata.
6. Done: Run focused tests, package the extension, and run project verification.
7. Done: Align the page adapter with Codex Browser patterns: observe first, reuse tab state, require unique locators for mutating actions, and return compact page signals after actions.

## Verification

- `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_browser_automate_queues_pending_job`
- `python -m unittest tests.test_cli_smoke.CliSmokeTests.test_browser_bridge_serves_and_completes_automation_job`
- `scripts\aiflow-dev.bat browser pack --force`
- `scripts\aiflow-dev.bat verify --auto --continue-on-error`
