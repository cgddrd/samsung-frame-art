#!/bin/bash

# Use full path to uv (crontab has minimal PATH)
UV_PATH="/home/zorin/.local/bin/uv"

VENV_NAME=".venv"
REQUIREMENTS_FILE="requirements.txt"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment: $VENV_NAME..."
    "$UV_PATH" venv "$VENV_NAME"
fi

# Install dependencies using uv (specify the venv's python)
echo "Installing dependencies with uv..."
"$UV_PATH" pip install --python "$VENV_NAME/bin/python" -r "$REQUIREMENTS_FILE"

echo "Running art.py with arguments: $@"
"$UV_PATH" run python3 art.py "$@"