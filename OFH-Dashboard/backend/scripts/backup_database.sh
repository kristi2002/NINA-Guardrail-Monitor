#!/bin/bash
# Database Backup Script for NINA Guardrail Monitor (Bash version)
# Simple wrapper for backup_database.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Activate virtual environment if it exists
if [ -d "$BACKEND_DIR/venv" ]; then
    source "$BACKEND_DIR/venv/bin/activate"
elif [ -d "$BACKEND_DIR/../venv" ]; then
    source "$BACKEND_DIR/../venv/bin/activate"
fi

# Run Python backup script
python "$SCRIPT_DIR/backup_database.py" "$@"

