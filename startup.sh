#!/bin/bash

# Make script executable
chmod +x "$0"

# Install ODBC Driver (these commands are handled by Azure App Service)
# The ODBC driver is pre-installed in the App Service environment

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

# Start app with gunicorn
gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=600 --log-level debug app:app
