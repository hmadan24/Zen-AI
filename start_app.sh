#!/bin/bash

# Kill any existing instances first
echo "Checking for existing instances..."
lsof -i :3002 | grep Python | awk '{print $2}' | xargs kill -9 2>/dev/null

# Wait a moment for ports to clear
sleep 1

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Start the application
echo "Starting Voice Assistant..."
python3 app.py 