#!/bin/bash
# macOS launcher for Job Radar CLI
# Opens Terminal and runs the job-radar executable

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/job-radar-cli"

# Use osascript to open Terminal and run the command
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd ~ && '$EXECUTABLE'; exit"
end tell
EOF
