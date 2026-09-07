# Setup Instructions

Complete step-by-step guide to set up the YouTube Audio Deduplication System.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Python Installation](#python-installation)
3. [FFmpeg Installation](#ffmpeg-installation)
4. [Chromaprint Installation](#chromaprint-installation)
5. [Project Setup](#project-setup)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## System Requirements

- **OS**: Windows 10+, macOS 10.12+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum (4GB+ recommended)
- **Disk Space**: 5GB+ for audio files
- **Internet**: Required for YouTube and API access

## Python Installation

### Windows

1. Download Python from https://www.python.org/downloads/
2. Run the installer
3. **Important**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```bash
   python --version
   ```

### macOS

Using Homebrew (recommended):
```bash
brew install python@3.11
```

Or download from https://www.python.org/downloads/

Verify:
```bash
python3 --version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
python3 --version
```

## FFmpeg Installation

FFmpeg is **required** for audio conversion.

### Windows (Method 1: Chocolatey - Easiest)

```bash
choco install ffmpeg
ffmpeg -version
```

### Windows (Method 2: Manual Download)

1. Visit https://ffmpeg.org/download.html
2. Download the Windows build
3. Extract to a folder (e.g., `C:\ffmpeg`)
4. Add `C:\ffmpeg\bin` to Windows PATH:
   - Right-click "This PC" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under System variables, select "Path" → Edit
   - Add `C:\ffmpeg\bin`
5. Verify: Open PowerShell and run:
   ```bash
   ffmpeg -version
   ```

### Windows (Method 3: Using conda)

```bash
conda install -c conda-forge ffmpeg
ffmpeg -version
```

### macOS

Using Homebrew:
```bash
brew install ffmpeg
ffmpeg -version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get install ffmpeg
ffmpeg -version
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install ffmpeg
ffmpeg -version
```

## Chromaprint Installation

**Optional but Recommended** - Enables audio fingerprinting.

### Windows (Chocolatey)

```bash
choco install chromaprint
fpcalc -version
```

### Windows (Manual Download)

1. Download from https://acoustid.org/chromaprint
2. Extract `fpcalc.exe`
3. Add to PATH or place in project directory

### macOS

```bash
brew install chromaprint
fpcalc -version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get install chromaprint-tools
fpcalc -version
```

## Project Setup

### Step 1: Clone/Download Project

```bash
cd d:\fellikehckrbutnt
# Project folder structure is ready
```

### Step 2: Create Virtual Environment (Recommended)

```bash
cd youtube_audio_dedup

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `yt-dlp` - YouTube downloader
- `pyacoustid` - Audio fingerprinting
- `librosa` - Audio analysis

### Step 4: Configure API Key (Optional)

For global duplicate detection:

1. Register at https://acoustid.org/api
2. Get your API key
3. Edit `config.py`:
   ```python
   ACOUSTID_API_KEY = "your_api_key_here"
   ```

### Step 5: Verify Installation

```bash
python -c "import yt_dlp; print('✓ yt-dlp installed')"
python -c "import acoustid; print('✓ pyacoustid installed')"
python -c "import librosa; print('✓ librosa installed')"

ffmpeg -version  # Should show FFmpeg version
fpcalc -version  # Should show Chromaprint version (if installed)
```

## Verification

Run the verification script:

```bash
python main.py
```

You should see the interactive menu. Try:
1. Start new download session
2. Enter a test keyword like "python"
3. Enter 3 for search count
4. Let it download a few files

If successful, all systems are working!

## Troubleshooting

### Python not found

**Problem**: `python is not recognized`

**Solution**:
```bash
# Windows: Use python3 instead
python3 --version

# Or add Python to PATH:
# Settings → Environment Variables → Add to PATH
```

### FFmpeg not found

**Problem**: `ffmpeg is not recognized` or `FFmpegNotFound`

**Solution**:
```bash
# Check if FFmpeg is installed
ffmpeg -version

# If not installed, use Chocolatey:
choco install ffmpeg

# Or add to PATH manually:
# Where you extracted FFmpeg: C:\ffmpeg\bin
# Add to Windows PATH environment variable
```

### Chromaprint/fpcalc not found

**Problem**: Warning about fpcalc, but system still works

**Solution**: This is optional. Install if you want audio fingerprinting:
```bash
choco install chromaprint
fpcalc -version
```

### yt-dlp import error

**Problem**: `ModuleNotFoundError: No module named 'yt_dlp'`

**Solution**:
```bash
pip install --upgrade yt-dlp

# Or reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Virtual environment issues

**Problem**: `venv` not found or not activated

**Solution**:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Check if activated (should see (venv) in prompt)
```

### Download fails with error

**Problem**: Videos won't download

**Solution**:
1. Check internet connection
2. Verify FFmpeg installation: `ffmpeg -version`
3. Try a different keyword
4. Check logs: `logs/youtube_dedup.log`
5. Some videos may be region-blocked or unavailable

### AcoustID API errors

**Problem**: `AcoustID API error` in logs

**Solution**:
- API key may be wrong
- Internet connection issue
- System will still work with local detection
- API is optional - not required for basic functionality

### Permissions error on Windows

**Problem**: `PermissionError: [Errno 13]` when writing files

**Solution**:
```bash
# Run PowerShell as Administrator
# Then:
python main.py
```

### Conda environment

**If using Anaconda/Miniconda instead of venv**:

```bash
# Create environment
conda create -n youtube_dedup python=3.11

# Activate
conda activate youtube_dedup

# Install FFmpeg
conda install -c conda-forge ffmpeg

# Install dependencies
pip install -r requirements.txt
```

## Post-Installation

### Recommended Steps

1. **Create API Key** (optional):
   - Register at https://acoustid.org/api
   - Add to `config.py`

2. **Test the System**:
   ```bash
   python main.py
   ```

3. **Check Logs**:
   ```bash
   # View recent logs
   tail -f logs/youtube_dedup.log
   ```

4. **Configure Settings** (if needed):
   - Edit `config.py`
   - Change `MAX_SEARCH_LIMIT`, duration ranges, etc.

5. **Create Backup Directory**:
   ```bash
   mkdir backups
   ```

## Next Steps

1. Read [README.md](README.md) for usage guide
2. Run `python main.py` to start using the system
3. Check [config.py](config.py) to customize settings
4. View logs in `logs/` folder for debugging

## Support

If you encounter issues:

1. **Check logs**:
   ```bash
   cat logs/youtube_dedup.log
   ```

2. **Verify installations**:
   ```bash
   python --version
   ffmpeg -version
   pip list  # Check all packages
   ```

3. **Reinstall dependencies**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **Check Windows PATH**:
   - Settings → System → Advanced system settings
   - Environment Variables → PATH
   - Ensure Python, FFmpeg, Chromaprint are listed

---

**Setup complete! You're ready to start downloading and deduplicating YouTube audio.** 🎵

For usage instructions, see [README.md](README.md)
