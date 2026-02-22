@echo off
echo Starting Log Inspector...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python tools\loginspector\main.py
pause
