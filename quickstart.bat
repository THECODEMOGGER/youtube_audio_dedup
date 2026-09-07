@echo off
REM YouTube Audio Deduplication System - Quick Start Script for Windows
REM This script sets up and runs the system with minimal user input

echo.
echo ========================================================================
echo  YouTube Audio Deduplication System - Quick Start
echo ========================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check FFmpeg installation
ffmpeg -version >nul 2>&1
ffprobe -version >nul 2>&1
if errorlevel 1 (
    echo ERROR: FFmpeg/FFprobe not found!
    echo Install with: choco install ffmpeg
    echo Or download from: https://www.ffmpeg.org/download.html
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo.
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Install/update dependencies
echo [SETUP] Installing dependencies (this may take a few minutes)...
pip install -q --upgrade pip
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Try running: pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Verify installations
echo [VERIFY] Checking installations...
python -c "import yt_dlp; print('  [OK] yt-dlp')" 2>nul || echo "  [!] yt-dlp not found"
python -c "import acoustid; print('  [OK] pyacoustid')" 2>nul || echo "  [!] pyacoustid not found"
python -c "import librosa; print('  [OK] librosa')" 2>nul || echo "  [!] librosa not found"
echo.

REM Run the system
echo ========================================================================
echo  STARTING SYSTEM
echo ========================================================================
echo.

python main.py

echo.
echo ========================================================================
echo  System closed
echo ========================================================================
pause
