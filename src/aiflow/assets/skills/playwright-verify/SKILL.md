---
name: playwright-verify
description: Use when frontend or UI work needs browser-based verification, screenshots, responsive checks, interaction testing, or Playwright setup through aiflow.
---

# Playwright Verify

## Purpose

Verify frontend behavior in a real browser with Playwright.

## Workflow

1. Confirm frontend tooling is installed:

```bat
aiflow frontend install
```

2. Start the configured dev server or ask the user for the URL.
3. Check desktop and mobile viewports.
4. Capture screenshots for changed screens.
5. Test the key user interactions touched by the change.
6. Record commands, screenshots, and issues.

## Project Commands

Install Playwright into project-local tools:

```bat
aiflow frontend install
```

Dry-run installation:

```bat
aiflow frontend install --dry-run
```

## Output

- URL checked
- Viewports checked
- Screenshots
- Interaction results
- Issues found
- Commands run
