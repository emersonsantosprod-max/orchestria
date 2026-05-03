#!/bin/bash
# Blocks Edit/Write that introduce forbidden imports per layer.
# - app/domain/**: no sqlite3, openpyxl, app.application, app.infrastructure
# - app/application/services/** (except pipeline.py): no sqlite3, openpyxl, app.infrastructure
python3 - <<'EOF'
import sys, json, re

data = json.load(sys.stdin)
tool_input = data.get("tool_input", {})
file_path = tool_input.get("file_path", "")
new_content = tool_input.get("new_string") or tool_input.get("content") or ""

is_domain = bool(re.search(r"/app/domain/[^/]+\.py$", file_path))
is_service = bool(re.search(r"/app/application/services/[^/]+\.py$", file_path))

if not is_domain and not is_service:
    sys.exit(0)

forbidden = []
if is_domain:
    forbidden = [
        "import sqlite3", "from sqlite3",
        "import openpyxl", "from openpyxl",
        "from app.application", "import app.application",
        "from app.infrastructure", "import app.infrastructure",
    ]
elif is_service and not file_path.endswith("pipeline.py"):
    forbidden = [
        "import sqlite3", "from sqlite3",
        "import openpyxl", "from openpyxl",
        "from app.infrastructure", "import app.infrastructure",
    ]

violations = [f for f in forbidden if f in new_content]
if violations:
    layer = "app/domain/" if is_domain else "app/application/services/"
    print(
        f"BLOCKED: {layer} forbidden imports detected:\n"
        + "\n".join(f"  - {v}" for v in violations)
        + "\nSee .claude/rules/boundary.md."
    )
    sys.exit(2)
sys.exit(0)
EOF
