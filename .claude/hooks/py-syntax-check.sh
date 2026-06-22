#!/bin/bash
# PostToolUse hook: check Python syntax after Write or Edit tool calls.
# Reads tool input JSON from stdin; exits 2 on syntax error so Claude sees the message.

python3 - <<'PYEOF'
import sys, json, subprocess

try:
    data = json.load(sys.stdin)
    fp = data.get("file_path", "")
    if not fp.endswith(".py"):
        sys.exit(0)

    result = subprocess.run(
        ["python3", "-m", "py_compile", fp],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Syntax error in {fp}:\n{result.stderr}", flush=True)
        sys.exit(2)
except Exception:
    pass  # never block on hook errors
PYEOF
