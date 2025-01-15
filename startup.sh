#!/bin/bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pandas openpyxl
gunicorn app:app
