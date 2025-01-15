@echo off
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Enabling wfastcgi...
%SYSTEMDRIVE%\Python311\python.exe -m wfastcgi-enable

echo Setup complete.
exit /b 0
