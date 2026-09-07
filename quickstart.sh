#!/bin/bash
# YouTube Audio Deduplication System - Quick Start Script for Unix/Linux/macOS
# This script sets up and runs the system with minimal user input

echo ""
echo "========================================================================"
echo "  YouTube Audio Deduplication System - Quick Start"
echo "========================================================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found!"
    echo "Please install Python from https://www.python.org/downloads/"
    echo "Or use your package manager:"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt-get install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "[OK] Python $PYTHON_VERSION found"
echo ""

# Check FFmpeg installation
if ! command -v ffmpeg &> /dev/null || ! command -v ffprobe &> /dev/null; then
    echo "ERROR: FFmpeg/FFprobe not found!"
    echo "Install with:"
    echo "  macOS: brew install ffmpeg"
    echo "  Linux: sudo apt-get install ffmpeg"
    echo "  Windows: choco install ffmpeg"
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[SETUP] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "[OK] Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "[SETUP] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi
echo "[OK] Virtual environment activated"
echo ""

# Install/update dependencies
echo "[SETUP] Installing dependencies (this may take a few minutes)..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Try running: pip install -r requirements.txt"
    exit 1
fi
echo "[OK] Dependencies installed"
echo ""

# Verify installations
echo "[VERIFY] Checking installations..."
python3 -c "import yt_dlp; print('  [OK] yt-dlp')" 2>/dev/null || echo "  [!] yt-dlp not found"
python3 -c "import acoustid; print('  [OK] pyacoustid')" 2>/dev/null || echo "  [!] pyacoustid not found"
python3 -c "import librosa; print('  [OK] librosa')" 2>/dev/null || echo "  [!] librosa not found"
echo ""

# Run the system
echo "========================================================================"
echo "  STARTING SYSTEM"
echo "========================================================================"
echo ""

python3 main.py

echo ""
echo "========================================================================"
echo "  System closed"
echo "========================================================================"
