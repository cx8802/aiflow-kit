# aiflow GUI

Tauri 2 desktop shell for the future Claude Code and Codex GUI in `aiflow-kit`.

## Scope

- React + Vite + TypeScript frontend in `src/`.
- Tauri 2 desktop host in `src-tauri/`.
- Initial desktop shell with project threads, a task composer, and review/verification inspection for Claude Code and Codex work.

The first scaffold does not call the Python CLI yet. Desktop commands and the local API boundary should be added after the GUI workflow and security boundary are explicit.

## Development

```powershell
cd apps/aiflow-gui
npm.cmd install
npm.cmd run dev
```

To run the desktop host, install the Tauri Windows prerequisites and Rust toolchain first, then run:

```powershell
cd apps/aiflow-gui
npm.cmd run tauri dev
```

Use `npm.cmd` on Windows when PowerShell execution policy blocks `npm.ps1`.
