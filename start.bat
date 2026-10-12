@echo off
title Smart Fault Detection - Underground Cable IoT System
color 0B
echo.
echo  ==============================================================
echo   ⚡ Smart Fault Detection in Underground Cables Using IoT
echo   📡 IoT Simulation System
echo   🎓 ECE Department - Final Year Project
echo  ==============================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Python is not installed or not in PATH!
    echo  📥 Download Python from: https://www.python.org/downloads/
    echo  ⚠  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo  ✓ Python found
echo.

:: Check if venv exists, create if not
if not exist "venv" (
    echo  📦 Creating virtual environment...
    python -m venv venv
    echo  ✓ Virtual environment created
    echo.
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install dependencies
echo  📦 Installing dependencies...
pip install -r requirements.txt --quiet
echo  ✓ Dependencies installed
echo.

:: Start the server
echo  🚀 Starting IoT Server...
echo  🌐 Open your browser at: http://localhost:5000
echo.
echo  Press Ctrl+C to stop the server
echo  ==============================================================
echo.

python app.py

pause
