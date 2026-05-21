# Implementation Plan

## Goal

Promote the browser companion into a Chrome/Edge extension platform where the extension is a lightweight connected browser surface and the project backend controls captures, selected elements, and automation queues.

## Non-goals

- Do not add browser-driven code edits, shell execution, agent runs, screenshots, or full-page HTML ingestion in this pass.
- Do not turn the browser companion into a third Claude Code or Codex plugin package.
- Do not write browser captures, selected elements, or bridge tokens outside the current project.
- Do not export logged-in website auth tokens, session cookies, localStorage, sessionStorage, request headers, or other raw browser credentials.
- Do not run background automation without a user action in the extension side panel.

## Impact Scope

- Browser platform design docs and extension README
- `.aiflow/config.toml` browser defaults and validation
- `aiflow browser` bridge health, packaging, automation queue, capture, and selected-element storage
- Chrome/Edge extension source tree and focused smoke coverage

## Steps

1. Simplify the extension side panel to the primary `connect -> select page element -> send to backend` workflow.
2. Keep capture, adapter action, and automation controls under an advanced section.
3. Add a temporary page element picker that highlights hovered elements and returns a bounded element summary.
4. Add token-gated `POST /elements` bridge support and project-local `.aiflow/browser/elements/` storage.
5. Update docs, README, config templates, and smoke tests for the selected-element flow.
6. Run configured verification and summarize remaining limits.

## Verification

- `npm run check` in `extensions/browser`
- `scripts\aiflow-dev.bat browser pack --force`
- `python -m unittest discover -s tests`
- `python -m compileall src`
- `scripts\aiflow-dev.bat verify --auto`
- `scripts\aiflow-dev.bat config check`
- `git diff --check`

## Risks

- Browser captures and selected element text may include sensitive page text, so scope and storage must stay explicit and project-local.
- localhost bridge requests need bounded payload size and a project token before accepting extension writes.
- Adapter actions can mutate live pages, so they must stay user-triggered and avoid raw credential export.
- Automation queues can affect live logged-in pages; they must remain inspectable JSON files and execute only after the user starts the extension path.
- Existing worktree changes are unrelated; keep browser companion edits scoped.
