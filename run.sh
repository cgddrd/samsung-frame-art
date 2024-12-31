#!/bin/bash

VENV_NAME=".env"
REQUIREMENTS_FILE="requirements.txt"

# Create a virtual environment
echo "Creating virtual environment: $VENV_NAME..."
python3 -m venv "$VENV_NAME"

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_NAME/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -r "$REQUIREMENTS_FILE"

echo "Running art.py with arguments: $@"
python3 art.py "$@"