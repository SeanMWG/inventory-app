#!/bin/bash
set -e

echo "Starting startup script..."

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y curl gnupg2 unixodbc-dev

# Install ODBC Driver
echo "Installing ODBC Driver..."
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
ACCEPT_EULA=Y apt-get install -y mssql-tools18

# Verify ODBC installation
echo "Verifying ODBC installation..."
odbcinst -j

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start the application with error logging
echo "Starting the application..."
gunicorn --bind=0.0.0.0:8000 \
         --timeout 600 \
         --log-level debug \
         --error-logfile /home/LogFiles/gunicorn-error.log \
         --access-logfile /home/LogFiles/gunicorn-access.log \
         --capture-output \
         app:app
