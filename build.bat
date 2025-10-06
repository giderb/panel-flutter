@echo off
REM Quick build script for NASTRAN Panel Flutter Analysis executable
REM This is a simple wrapper around build_executable.py

echo.
echo ==========================================
echo  NASTRAN Panel Flutter Analysis
echo  Executable Build Script
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please create virtual environment first:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo   .venv\Scripts\pip install pyinstaller
    echo.
    pause
    exit /b 1
)

REM Run the Python build script
echo Running build script...
echo.

.venv\Scripts\python.exe build_executable.py %*

echo.
echo Build script finished.
echo.
pause
