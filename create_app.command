#!/bin/bash
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Activate the virtual environment
source venv/bin/activate

# Run the Python app builder script
python create_launcher.py

# Deactivate the virtual environment
deactivate

# Wait for a keypress before closing the terminal window
echo ""
echo "Press any key to close this window..."
read -n 1 -s 