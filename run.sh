#!/bin/bash

VENV_NAME=".venv"
REQUIREMENTS_FILE="requirements.txt"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment: $VENV_NAME..."
    uv venv "$VENV_NAME"
fi

# Install dependencies using uv (specify the venv's python)
echo "Installing dependencies with uv..."
uv pip install --python "$VENV_NAME/bin/python" -r "$REQUIREMENTS_FILE"

echo "Running art.py with arguments: $@"
uv run python3 art.py "$@"