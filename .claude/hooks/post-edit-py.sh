#!/bin/bash
# Runs ruff check + layer boundary tests after editing app/ or tests/ Python files.
python3 - <<'EOF'
import sys, json, re, subprocess

data = json.load(sys.stdin)
tool_input = data.get("tool_input", {})
file_path = tool_input.get("file_path", "")

if not re.search(r"/(app|tests)/.*\.py$", file_path):
    sys.exit(0)

output_parts = []

ruff = subprocess.run(
    ["python", "-m", "ruff", "check", file_path],
    capture_output=True, text=True
)
if ruff.returncode != 0:
    output_parts.append(f"ruff:\n{(ruff.stdout + ruff.stderr).strip()}")

boundary = subprocess.run(
    ["python", "-m", "pytest", "tests/test_layer_boundaries.py", "-q", "--tb=short"],
    capture_output=True, text=True
)
if boundary.returncode != 0:
    output_parts.append(f"boundary tests:\n{(boundary.stdout + boundary.stderr).strip()}")

if output_parts:
    print("Post-edit checks failed:\n" + "\n\n".join(output_parts))

sys.exit(0)  # report only, never block
EOF
