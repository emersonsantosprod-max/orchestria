#!/bin/bash
# Blocks edits to app/domain/ that introduce forbidden imports.
python3 - <<'EOF'
import sys, json, re

data = json.load(sys.stdin)
tool_input = data.get("tool_input", {})
file_path = tool_input.get("file_path", "")
new_content = tool_input.get("new_string") or tool_input.get("content") or ""

if not re.search(r"/app/domain/[^/]+\.py$", file_path):
    sys.exit(0)

forbidden = [
    "import sqlite3", "from sqlite3",
    "import openpyxl", "from openpyxl",
    "from app.application", "import app.application",
    "from app.infrastructure", "import app.infrastructure",
]
violations = [f for f in forbidden if f in new_content]
if violations:
    print(
        "BLOCKED: app/domain/ forbidden imports detected:\n"
        + "\n".join(f"  - {v}" for v in violations)
        + "\nSee .claude/rules/boundary.md for allowed imports."
    )
    sys.exit(2)
sys.exit(0)
EOF
