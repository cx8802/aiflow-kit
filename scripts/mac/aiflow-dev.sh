#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AIFLOW_KIT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

if [ -n "${AIFLOW_PYTHON:-}" ]; then
  PYTHON_BIN=$AIFLOW_PYTHON
elif [ -x "$AIFLOW_KIT_ROOT/.venv/bin/python" ]; then
  PYTHON_BIN="$AIFLOW_KIT_ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo "python3 or python is required to run aiflow." >&2
  exit 1
fi

export AIFLOW_KIT_ROOT
PYTHONPATH="$AIFLOW_KIT_ROOT/packages/aiflow-cli/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPATH

exec "$PYTHON_BIN" -m aiflow "$@"
