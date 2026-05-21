# Plan

Add a backend-driven browser automation path to the Chrome/Edge extension.

## Scope

- Keep browser automation jobs controlled by the project backend queue.
- Let the extension configuration page trigger the next queued job without accepting a manual URL.
- Open backend-provided URLs in a real browser tab and run extract/click/fill/wait steps there.
- Keep sensitive browser data out of captures: no cookies, localStorage, sessionStorage, raw headers, request bodies, or response bodies.

## Steps

1. Add a configuration-page automation action and result area.
2. Implement a settings-page automation runner using `chrome.tabs` and `chrome.scripting`.
3. Expose the shared in-page adapter to injected scripts.
4. Update extension documentation for the new trigger path.
5. Run extension checks and project verification.
