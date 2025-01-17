#!/bin/bash

# Install ODBC Driver
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install dependencies
pip install -r requirements.txt

# Start app with gunicorn
gunicorn --bind=0.0.0.0:8000 app:app
