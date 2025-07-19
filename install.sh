#!/bin/bash

# This script sets up the OmniForge project.
# It creates a Python virtual environment and installs all necessary dependencies.

set -e

PYTHON_CMD="python3"
VENV_DIR=".venv"

echo ">>> Setting up OmniForge..."

# Check if Python is available
if ! command -v $PYTHON_CMD &> /dev/null
then
    echo "ERROR: $PYTHON_CMD could not be found. Please install Python 3."
    exit 1
fi

# Create the virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo ">>> Creating Python virtual environment in '$VENV_DIR'..."
    $PYTHON_CMD -m venv $VENV_DIR
else
    echo ">>> Virtual environment already exists."
fi

# Activate the environment and install dependencies
echo ">>> Activating environment and installing dependencies from requirements.txt..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# Make the main executable script runnable
chmod +x omni

echo ""
echo "✅ Setup complete!"
echo "To run OmniForge, first activate the environment:"
echo "source $VENV_DIR/bin/activate"
echo ""
echo "Then, run the main script:"
echo "./omni"