#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Setting up Web3 DevOps Toolkit..."

# Check for Python
if ! command -v python3 &> /dev/null
then
    echo "Error: python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check for npm
if ! command -v npm &> /dev/null
then
    echo "Error: npm is not installed. Please install Node.js and npm."
    exit 1
fi

# Python environment setup (create/use venv if not already in one)
if [ -z "$VIRTUAL_ENV" ]; then
    if [ ! -d ".venv" ]; then
        echo "Creating Python virtual environment (.venv)..."
        python3 -m venv .venv
    fi
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies for contracts
echo "Installing Node.js dependencies for contracts..."
(cd contracts && npm install)
ln -sf ../contracts/node_modules scripts/node_modules

echo "Setup complete. Running example pipeline..."

# Run the example pipeline
python3 src/cli.py run-pipeline --pipeline ./pipelines/example_pipeline.yaml

echo "Web3 DevOps Toolkit finished."
