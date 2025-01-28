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

# Start app with wfastcgi
wfastcgi-enable
