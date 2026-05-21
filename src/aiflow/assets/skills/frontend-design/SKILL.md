---
name: frontend-design
description: Use when the user asks to design or substantially improve UI, create a polished frontend screen, build a design system, avoid generic AI-looking pages, or translate product intent into high-quality visual and interaction design.
---

# Frontend Design

## Purpose

Design and implement frontend UI that is useful, polished, responsive, and consistent with the project.

## Workflow

1. Identify the product type, target user, and primary workflow.
2. Inspect existing framework, design system, component library, routes, and styling conventions.
3. Design the actual usable screen first, not a marketing landing page unless requested.
4. Use restrained, domain-appropriate layout, spacing, typography, color, and interaction states.
5. Prefer existing components and icons.
6. Include expected states: loading, empty, error, disabled, hover/focus, mobile, desktop.
7. Hand off to `playwright-verify` or `frontend-verify` for browser checks.

## Rules

- Do not create generic gradient hero pages for product tools or admin systems.
- Do not put cards inside cards.
- Do not rely on one-note palettes.
- Do not use visible instructional text to explain how the UI works.
- Make text fit at mobile and desktop sizes.
- Use project assets or generated bitmap assets when a visual experience needs imagery.

## Output

- Design intent
- Affected files
- Components and states
- Responsive behavior
- Verification plan
