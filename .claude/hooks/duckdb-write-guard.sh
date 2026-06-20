#!/bin/bash
# PreToolUse hook: block Write/Edit calls that open DuckDB without read_only=True in api/ files.
# Reads tool input JSON from stdin; exits 2 to block the tool call with an explanation.

python3 - <<'PYEOF'
import sys, json, re

try:
    data = json.load(sys.stdin)
    fp = data.get("file_path", "")

    # Only guard api/ directory
    if "/api/" not in fp and not fp.startswith("api/"):
        sys.exit(0)

    # Get the content being written
    content = data.get("content", "") + data.get("new_string", "")

    # Find duckdb.connect() calls
    connects = re.findall(r"duckdb\.connect\([^)]*\)", content)
    for call in connects:
        if "read_only=True" not in call:
            print(
                f"BLOCKED: {fp} contains a duckdb.connect() call without read_only=True.\n"
                f"  Found: {call}\n"
                f"  The API must never open DuckDB in write mode. "
                f"Change to: duckdb.connect(DB_PATH, read_only=True)",
                flush=True,
            )
            sys.exit(2)
except Exception:
    pass  # never block on hook errors
PYEOF
