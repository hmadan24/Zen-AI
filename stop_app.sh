#!/bin/bash

# Find and kill any processes running on port 3002
echo "Stopping Flask application..."
lsof -i :3002 | grep Python | awk '{print $2}' | xargs kill -9 2>/dev/null

# Verify the port is clear
if lsof -i :3002 > /dev/null; then
    echo "Failed to stop the application. Please check manually."
else
    echo "Application stopped successfully."
fi 