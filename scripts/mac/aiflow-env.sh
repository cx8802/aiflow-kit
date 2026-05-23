#!/usr/bin/env sh

if [ -n "${BASH_SOURCE:-}" ]; then
  AIFLOW_ENV_SCRIPT=$BASH_SOURCE
elif [ -n "${ZSH_VERSION:-}" ]; then
  eval 'AIFLOW_ENV_SCRIPT=${(%):-%x}'
else
  AIFLOW_ENV_SCRIPT=$0
fi

AIFLOW_ENV_DIR=$(CDPATH= cd -- "$(dirname -- "$AIFLOW_ENV_SCRIPT")" && pwd)
export AIFLOW_KIT=$(CDPATH= cd -- "$AIFLOW_ENV_DIR/../.." && pwd)
export AIFLOW_KIT_ROOT="$AIFLOW_KIT"
export PATH="$AIFLOW_KIT/scripts/mac:$PATH"

echo "aiflow current shell session is ready."
echo
echo "AIFLOW_KIT=$AIFLOW_KIT"
echo "AIFLOW_KIT_ROOT=$AIFLOW_KIT_ROOT"
echo "PATH prepended with: $AIFLOW_KIT/scripts/mac"
echo "The PATH entry exposes: aiflow and aiflow-install"
echo
echo "From any project directory, run:"
echo "  aiflow-install"
echo
echo "This script only changes the current shell session when sourced."
