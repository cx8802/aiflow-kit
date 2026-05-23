# aiflow CLI

Python CLI package for the `aiflow-kit` workspace.

The repository-level documentation lives in the root `README.md`. This package contains the distributable `aiflow` command, bundled templates, and bundled skills.

Install it into the workspace virtual environment during development:

```bat
cd /d <aiflow-kit>
if not exist .venv\Scripts\python.exe python -m venv .venv
.venv\Scripts\python.exe -m pip install -e packages\aiflow-cli
```

Avoid installing this package into the system Python environment while the project is still evolving.
