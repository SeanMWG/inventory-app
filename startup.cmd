@echo off
echo Installing dependencies...

:: Install Python packages
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Download and install ODBC Driver
echo Installing ODBC Driver...
powershell -Command "Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/?linkid=2249006' -OutFile 'msodbcsql.msi'"
msiexec /i msodbcsql.msi IACCEPTMSODBCSQLLICENSETERMS=YES /qn
del msodbcsql.msi

:: Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=production

:: Start Flask app
echo Starting Flask app...
python -m flask run --host=0.0.0.0 --port=8000
