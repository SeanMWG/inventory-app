#!/bin/bash

# Install ODBC Driver
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install dependencies
pip install -r requirements.txt

# Debug info
echo "Current directory: $(pwd)"
echo "Listing files:"
ls -la
echo "Listing static directory:"
ls -la static/

# Start app with gunicorn
gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=600 --log-level debug app:app
