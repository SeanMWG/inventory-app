#!/bin/bash

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Debug info
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
echo "Listing files:"
ls -la
echo "Listing static directory:"
ls -la static/

# Debug environment variables (without exposing sensitive data)
echo "Checking DATABASE_URL environment variable:"
if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL is set"
else
    echo "WARNING: DATABASE_URL is not set"
fi

# Start app with wfastcgi
wfastcgi-enable
