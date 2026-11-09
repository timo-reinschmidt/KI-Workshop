@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 ki_workshop.py
) else (
  python ki_workshop.py
)
pause
