@echo off
echo Installing ODBC Driver...

REM Download ODBC Driver
powershell -Command "Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/?linkid=2249006' -OutFile 'msodbcsql.msi'"

REM Install ODBC Driver silently
msiexec /i msodbcsql.msi IACCEPTMSODBCSQLLICENSETERMS=YES /qn

REM Clean up
del msodbcsql.msi

echo ODBC Driver installation complete.

REM Start the Python app using the Azure Web App's Python
D:\home\python311\python.exe -m flask run --host=0.0.0.0 --port=8000
