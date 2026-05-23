#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AIFLOW_KIT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

AIFLOW_SKIP_RULES=0
AIFLOW_NO_CONTEXT=0
AIFLOW_INIT_CONTEXT_ARG=""

usage() {
  echo "Usage: aiflow-install [--skip-rules] [--no-context]"
  echo
  echo "Install aiflow-kit into the current project directory."
  echo
  echo "Options:"
  echo "  --skip-rules   Do not generate AGENTS.md or CLAUDE.md."
  echo "  --no-context   Skip context generation."
  echo "  -h, --help     Show this help."
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --skip-rules)
      AIFLOW_SKIP_RULES=1
      ;;
    --no-context)
      AIFLOW_NO_CONTEXT=1
      AIFLOW_INIT_CONTEXT_ARG="--no-context"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

echo "aiflow-kit: $AIFLOW_KIT_ROOT"
echo "target project: $(pwd)"
echo

if [ "$AIFLOW_SKIP_RULES" = "1" ]; then
  "$AIFLOW_KIT_ROOT/scripts/mac/aiflow-dev.sh" init --no-codex --no-claude $AIFLOW_INIT_CONTEXT_ARG
else
  "$AIFLOW_KIT_ROOT/scripts/mac/aiflow-dev.sh" init $AIFLOW_INIT_CONTEXT_ARG
fi
if [ "$?" -ne 0 ]; then
  exit 1
fi

"$AIFLOW_KIT_ROOT/scripts/mac/aiflow-dev.sh" install-skills
if [ "$?" -ne 0 ]; then
  exit 1
fi

"$AIFLOW_KIT_ROOT/scripts/mac/aiflow-dev.sh" env detect
if [ "$?" -ne 0 ]; then
  exit 1
fi

if [ "$AIFLOW_NO_CONTEXT" = "0" ]; then
  "$AIFLOW_KIT_ROOT/scripts/mac/aiflow-dev.sh" context --compact
  if [ "$?" -ne 0 ]; then
    exit 1
  fi
fi

"$AIFLOW_KIT_ROOT/scripts/mac/aiflow-dev.sh" verify --auto --dry-run
if [ "$?" -ne 0 ]; then
  exit 1
fi

echo
echo "aiflow project install complete."
echo
echo "Next commands:"
echo "  aiflow workflow start \"your task\""
echo "  aiflow workflow db list"
