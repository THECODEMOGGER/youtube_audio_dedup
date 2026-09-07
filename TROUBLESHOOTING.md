# Troubleshooting Guide

Complete troubleshooting guide for the YouTube Audio Deduplication System.

## Quick Diagnostics

Run this to check your setup:

```bash
# Check Python
python --version

# Check FFmpeg
ffmpeg -version

# Check Chromaprint
fpcalc -version

# Check Python packages
pip list | grep -E "yt-dlp|acoustid|librosa"
```

## Common Issues and Solutions

### Python & Setup Issues

#### Problem: "ModuleNotFoundError: No module named 'yt_dlp'"

**Causes**:
- Dependencies not installed
- Virtual environment not activated
- Wrong Python version

**Solutions**:
```bash
# Install dependencies
pip install -r requirements.txt

# Or install manually
pip install yt-dlp pyacoustid librosa

# Check Python version (should be 3.8+)
python --version

# If using virtual environment, ensure it's activated
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
```

#### Problem: "python: command not found"

**Causes**:
- Python not installed
- Python not in PATH
- Using wrong Python command

**Solutions**:
```bash
# Try python3 instead
python3 --version

# Windows: May need full path
C:\Python\python.exe --version

# Add Python to PATH
# Settings → Environment Variables → Edit PATH
```

#### Problem: Virtual environment not working

**Signs**:
- Prompt doesn't show `(venv)`
- Still getting import errors
- pip install fails

**Solutions**:
```bash
# Windows - Recreate virtual environment
rmdir /s /q venv
python -m venv venv
venv\Scripts\activate

# Linux/macOS - Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### Dependency Issues

#### Problem: "No module named 'yt_dlp' after pip install"

**Causes**:
- Installation incomplete
- Wrong Python/pip version
- Virtual environment deactivated

**Solutions**:
```bash
# Force reinstall
pip install --force-reinstall yt-dlp

# Install with verbose output to see errors
pip install -v yt-dlp

# Check pip is using correct Python
pip --version

# Should show same Python as 'python --version'
```

#### Problem: "pip: command not found"

**Causes**:
- Python not in PATH
- pip not installed with Python

**Solutions**:
```bash
# Use python -m pip
python -m pip --version

# Or python3 -m pip
python3 -m pip --version

# Upgrade pip
python -m pip install --upgrade pip
```

### FFmpeg Issues

#### Problem: "FFmpeg not found" or "FFmpegNotFound"

**Causes**:
- FFmpeg not installed
- Not in system PATH
- Wrong installation

**Solutions**:
```bash
# Windows - Install via Chocolatey
choco install ffmpeg

# If not using Chocolatey, manual install:
# 1. Download from https://ffmpeg.org/download.html
# 2. Extract to folder (e.g., C:\ffmpeg)
# 3. Add C:\ffmpeg\bin to PATH
# 4. Verify: ffmpeg -version

# macOS
brew install ffmpeg

# Linux Ubuntu/Debian
sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
```

#### Problem: "FFmpeg version too old"

**Causes**:
- Outdated FFmpeg installation

**Solutions**:
```bash
# Update FFmpeg
# Windows: choco upgrade ffmpeg
# macOS: brew upgrade ffmpeg
# Linux: sudo apt-get install --upgrade ffmpeg

# Check version
ffmpeg -version
# Should be recent (2020+)
```

### Chromaprint Issues

#### Problem: "fpcalc not found" or fingerprinting disabled

**Causes**:
- Chromaprint not installed
- Not in PATH
- Optional (system still works without it)

**Solutions**:
```bash
# Install Chromaprint
# Windows: choco install chromaprint
# macOS: brew install chromaprint
# Linux: sudo apt-get install chromaprint-tools

# Verify
fpcalc -version

# Note: System works without it, but fingerprinting uses fallback
```

### YouTube Download Issues

#### Problem: "Download failed" or "Video not available"

**Causes**:
- Video region-blocked
- Video removed or private
- Network connection issue
- yt-dlp outdated

**Solutions**:
```bash
# Update yt-dlp (formats change frequently)
pip install --upgrade yt-dlp

# Test with a known-good video
# Try: python main.py
# Search: "python tutorial"

# Check network
ping youtube.com  # Should respond

# Check specific video
python -c "from yt_dlp import YoutubeDL; ydl = YoutubeDL(); ydl.extract_info('https://www.youtube.com/watch?v=VIDEO_ID', download=False)"

# If error appears, video may be unavailable
```

#### Problem: "HTTP Error 403" or "Video unavailable"

**Causes**:
- Video region-blocked
- Geofencing
- Video deleted
- YouTube blocking bot access

**Solutions**:
```bash
# Usually transient - just try again
python main.py

# Try with VPN (if region-blocked)

# Update yt-dlp (YouTube changes defenses frequently)
pip install --upgrade yt-dlp

# Add delay between downloads in config.py
# Some ISP/YT implementations rate-limit aggressive downloads
```

#### Problem: "No videos found"

**Causes**:
- Invalid keyword
- YouTube search broken (rare)
- Keyword too specific

**Solutions**:
```bash
# Try different keyword
# "python tutorial" → "python"
# "very specific topic" → More general term

# Check logs for error
# logs/youtube_dedup.log

# Verify YouTube works
# Try in web browser: youtube.com/results?search_query=python

# Update yt-dlp
pip install --upgrade yt-dlp
```

### Audio Processing Issues

#### Problem: "Audio conversion failed" or "MP3 not created"

**Causes**:
- FFmpeg not installed
- Corrupted audio file
- Insufficient disk space
- Permission issues

**Solutions**:
```bash
# Verify FFmpeg
ffmpeg -version

# Check disk space
# Windows: Check C: drive free space
# Linux: df -h

# Check permissions
# Make sure downloads/ folder is writable

# Try manual FFmpeg test
ffmpeg -i "downloads/test.webm" -acodec libmp3lame -q:a 5 "downloads/test.mp3"

# Check logs
cat logs/youtube_dedup.log | grep -i ffmpeg
```

#### Problem: "Audio file too short for fingerprinting"

**Causes**:
- Audio less than 3 seconds (config setting)
- Incomplete download

**Solutions**:
```bash
# Check file
# Listen to verify it's complete

# Change threshold in config.py if needed
# FINGERPRINT_MIN_DURATION = 3  # seconds

# File is still saved, fingerprinting just skipped
# This is not an error condition
```

### Deduplication Issues

#### Problem: "False positives" - removing non-duplicate files

**Causes**:
- Title similarity threshold too low
- Two different songs with similar titles

**Solutions**:
```bash
# Increase similarity threshold in config.py
# Default: TITLE_SIMILARITY_THRESHOLD = 0.85
# Try: 0.90 or 0.95

# Check your fingerprint database
python -c "from database import FingerprintDatabase; db = FingerprintDatabase(); print(db.get_stats())"

# View specific fingerprints if needed
```

#### Problem: "False negatives" - duplicate not detected

**Causes**:
- Title similarity threshold too high
- Different titles (remix, cover, version)
- Fingerprinting not enabled

**Solutions**:
```bash
# Lower similarity threshold
# TITLE_SIMILARITY_THRESHOLD = 0.80  # More permissive

# Check Chromaprint is installed
fpcalc -version

# Files are still downloaded, duplicates just aren't detected
# Not critical - you caught them in this run
```

### API Issues

#### Problem: "AcoustID API error" or "API key invalid"

**Causes**:
- API key not set
- API key invalid
- Rate limiting
- Network issue

**Solutions**:
```bash
# Register at https://acoustid.org/api
# Add key to config.py

# Verify key
# In config.py: ACOUSTID_API_KEY = "your_key_here"

# API is optional - system works without it
# Check logs for specific error

# If rate-limited, wait and retry
```

#### Problem: "Too many API requests"

**Causes**:
- Querying API too frequently
- Multiple instances running

**Solutions**:
```bash
# AcoustID API calls are rate-limited
# Just retry after a few minutes

# Only one instance of system should run at a time

# Files are still saved, just can't query API
```

### Database Issues

#### Problem: "Database corrupted" or JSON parse error

**Causes**:
- Corrupted fingerprints.json file
- Interrupted write during save
- Permission issues

**Solutions**:
```bash
# Backup current database
cp fingerprints.json fingerprints.json.backup

# Clear database (warning: loses fingerprints)
python -c "from database import FingerprintDatabase; db = FingerprintDatabase(); db.clear_database()"

# System will recreate it on next run

# Or restore from backup
cp fingerprints.json.backup fingerprints.json
```

#### Problem: "Cannot write to database"

**Causes**:
- Permission denied
- Disk full
- Database file locked

**Solutions**:
```bash
# Check permissions
# Make sure you have write access to project folder

# Check disk space
# Need at least 1GB free

# Restart system
# Closes any file locks

# Move project to different location if permission issues
```

### Performance Issues

#### Problem: "Downloads are slow"

**Causes**:
- Slow internet connection
- YouTube throttling downloads
- Too many concurrent connections
- Antivirus/firewall blocking

**Solutions**:
```bash
# Reduce concurrent downloads in config.py
# MAX_CONCURRENT_DOWNLOADS = 2  # Was 5

# Increase timeout
# DOWNLOAD_TIMEOUT = 600  # seconds

# Check internet connection
ping 8.8.8.8

# Disable antivirus scanning for downloads folder
# Disable VPN if using one
```

#### Problem: "System is freezing or unresponsive"

**Causes**:
- Too many concurrent operations
- Not enough RAM
- Audio processing taking too long

**Solutions**:
```bash
# Reduce concurrent downloads
# MAX_CONCURRENT_DOWNLOADS = 1

# Restart system and clear memory

# Process fewer videos at a time
# Reduce search count from 100 to 10

# Check system resources
# Task Manager (Windows) or Activity Monitor (macOS)
```

### Logging & Debugging

#### How to view detailed logs

```bash
# View all logs
cat logs/youtube_dedup.log

# View last 50 lines
tail -n 50 logs/youtube_dedup.log

# Watch logs in real-time (Linux/macOS)
tail -f logs/youtube_dedup.log

# Search for errors
grep ERROR logs/youtube_dedup.log

# Search for specific issue
grep "DownloadError" logs/youtube_dedup.log
```

#### Enable debug logging

Edit `config.py`:
```python
LOG_LEVEL = "DEBUG"  # Instead of "INFO"
```

This provides much more detailed output.

## Stress Testing

If having issues, try this minimal test:

```bash
# Test 1: Can Python import modules?
python -c "import yt_dlp; print('OK')"
python -c "import acoustid; print('OK')"

# Test 2: Does FFmpeg work?
ffmpeg -h > /dev/null && echo "FFmpeg OK"

# Test 3: Can we search YouTube?
python -c "
from downloader import YouTubeDownloader
dl = YouTubeDownloader()
videos = dl.search_videos('python', 3)
print(f'Found {len(videos)} videos')
"

# Test 4: Can we download a small file?
python -c "
from downloader import YouTubeDownloader
from pathlib import Path
dl = YouTubeDownloader()
videos = dl.search_videos('short', 1)
if videos:
    result = dl.download_audio(videos[0]['url'], videos[0]['id'], 'test')
    print(f'Download result: {result}')
"
```

## When to Seek Help

If after trying these solutions the issue persists:

1. **Check logs**: `logs/youtube_dedup.log` contains error details
2. **Note error message**: Exactly what does it say?
3. **Your system**: 
   - OS version
   - Python version: `python --version`
   - FFmpeg version: `ffmpeg -version`
4. **Reproducibility**: Can you recreate the issue?

## Getting the Most Help

Include:
```
OS: Windows 10/macOS/Linux
Python: 3.9
Error message: [exact error text]
Last log lines: [from logs/youtube_dedup.log]
Search term: [what you were searching for]
Steps to reproduce: [what you did exactly]
```

## Support Resources

- **FFmpeg Documentation**: https://ffmpeg.org/documentation.html
- **yt-dlp GitHub**: https://github.com/yt-dlp/yt-dlp
- **AcoustID Documentation**: https://acoustid.org/
- **Python Docs**: https://docs.python.org/3/

---

**Still stuck?** Check [README.md](README.md) for more details or review the [SETUP.md](SETUP.md) guide.
