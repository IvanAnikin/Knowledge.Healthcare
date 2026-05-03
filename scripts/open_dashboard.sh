#!/usr/bin/env bash
# scripts/open_dashboard.sh
#
# Regenerate the static task dashboard and open it in the default browser.
# Run from the repository root:
#
#   bash scripts/open_dashboard.sh
#
# Requires: Python 3.8+, macOS (uses `open`)

set -euo pipefail

GENERATOR="scripts/generate_dashboard.py"
OUTPUT="dashboards/task-dashboard.html"

# 1. Verify the generator exists
if [[ ! -f "$GENERATOR" ]]; then
  echo "Error: $GENERATOR not found. Aborting." >&2
  exit 1
fi

# 2. Run the generator
echo "Generating dashboard..."
python3 "$GENERATOR"

# 3. Verify the output file was created
if [[ ! -s "$OUTPUT" ]]; then
  echo "Error: $OUTPUT was not created or is empty after generation." >&2
  exit 1
fi

echo "Dashboard generated: $OUTPUT"

# 4. Open in browser
if open "$OUTPUT"; then
  echo "Opened in browser."
else
  echo "Warning: Could not open browser automatically. Open $OUTPUT manually." >&2
  exit 1
fi
