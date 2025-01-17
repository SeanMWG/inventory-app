#!/bin/bash

# Make script executable in case permissions were lost
chmod +x "$0"

# Install system dependencies
echo "Installing system dependencies..."
curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc
curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list

# Update package list and install ODBC driver
echo "Installing ODBC driver..."
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
ACCEPT_EULA=Y apt-get install -y mssql-tools18
apt-get install -y unixodbc-dev

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Log environment for debugging
echo "Environment variables:"
env | grep -v PASSWORD | grep -v KEY

# Start app with gunicorn
echo "Starting application..."
gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app
