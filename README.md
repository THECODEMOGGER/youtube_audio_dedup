# YouTube Audio Deduplication System

A production-quality Python system for downloading YouTube videos, filtering them intelligently, and removing duplicates using both title similarity analysis and audio fingerprinting.

## Features

✅ **Smart YouTube Search**
- Search YouTube with custom keywords
- Dynamic result count (1-200, safely capped)
- Parallel downloading with ThreadPoolExecutor

✅ **Intelligent Filtering**
- Keyword matching in video titles
- Duration filtering (1-10 minutes customizable)
- Title similarity detection (removes near-duplicate titles)

✅ **Audio Processing**
- Downloads best quality audio
- Automatic MP3 conversion with FFmpeg
- Configurable bitrate (default 192 kbps)

✅ **Advanced Deduplication**
- **File Hash Comparison** - Instant detection of exact duplicates
- **Audio Fingerprinting** - Chromaprint-based similarity detection
- **AcoustID Integration** - Global duplicate detection via API
- **Local Database** - Stores fingerprints to avoid reprocessing

✅ **Error Handling**
- Graceful input validation with safe defaults
- Download retry mechanism (up to 3 attempts)
- Comprehensive error logging
- Automatic cleanup of duplicates

✅ **User-Friendly**
- Interactive menu system
- Progress tracking and statistics
- Detailed console feedback with emojis
- Beautiful formatted output

## Architecture

```
project/
├── main.py                 # Entry point and system orchestrator
├── config.py              # Configuration and constants
├── utils.py               # Utility functions (validation, logging, etc.)
├── database.py            # Fingerprint storage and retrieval
├── downloader.py          # yt-dlp integration for YouTube
├── filter.py              # Video filtering logic
├── fingerprint.py         # Audio fingerprinting and duplicate detection
├── downloads/             # Downloaded audio files (auto-created)
├── fingerprints.json      # Local fingerprint database (auto-created)
├── logs/                  # Log files (auto-created)
└── README.md              # This file
```

## Installation

### Basic setup

1. Install Python 3.9 or newer.
2. Download or clone the project.
3. Run:

```bash
python main.py
```

On first launch, the app automatically checks the current Python environment, installs missing Python packages from `requirements.txt`, downloads local FFmpeg/FFprobe binaries if needed, and downloads a local `fpcalc` copy when the project requires it.

> An internet connection is required for the first-time automatic setup.

### What the bootstrapper installs

- Python runtime packages from `requirements.txt`
- Local FFmpeg and FFprobe binaries inside the project under `tools/ffmpeg/`
- Local Chromaprint `fpcalc` if it is needed for audio fingerprinting, stored under `tools/chromaprint/`

The bootstrapper prepends the local tool directory to `PATH` so the application can use the downloaded binaries without requiring a system-wide installation.

### Manual configuration (optional)

If you want to use an AcoustID API key for global duplicate detection:

1. Register at https://acoustid.org/api
2. Get your API key
3. Edit `config.py` and set:
   ```python
   ACOUSTID_API_KEY = "your_api_key_here"
   ```

### Dependencies handled automatically

- `yt-dlp` via `python -m pip install`
- `pyacoustid` via `python -m pip install`
- `librosa` via `python -m pip install`
- `mutagen` via `python -m pip install`
- `ffmpeg` / `ffprobe` via official upstream builds downloaded into the project
- `fpcalc` via local Chromaprint download when required

### If setup fails

The app will show a clear error instead of a traceback when:

- Python is too old
- a package cannot be installed because there is no internet connection
- FFmpeg or `fpcalc` cannot be downloaded or extracted
- the platform is unsupported

After fixing the issue, run `python main.py` again.

To use global duplicate detection via AcoustID:

1. Register at https://acoustid.org/api-key
2. Get your API key
3. Edit `config.py` and set:
   ```python
   ACOUSTID_API_KEY = "your_api_key_here"
   ```

## Configuration

Edit `config.py` to customize:

```python
# Limits
MAX_SEARCH_LIMIT = 200              # Hard cap on search results
DEFAULT_SEARCH_COUNT = 10            # Default search count

# Duration (seconds)
MIN_DURATION_SECONDS = 60            # 1 minute
MAX_DURATION_SECONDS = 600           # 10 minutes

# Similarity Threshold (0.0 to 1.0)
TITLE_SIMILARITY_THRESHOLD = 0.85    # 85% match = duplicate

# Download Settings
MAX_CONCURRENT_DOWNLOADS = 5         # Parallel downloads
AUDIO_BITRATE = "192"                # kbps

# API
ACOUSTID_API_KEY = "YOUR_KEY_HERE"  # For global duplicate detection
```

## Usage

### Quick Start

```bash
python main.py
```

### Interactive Menu

The system provides an interactive menu:

```
1. Start new download session
2. View database statistics
3. List downloaded files
4. Clear database
5. Exit
```

### Workflow Example

```
Enter keyword: "python tutorial"
How many top results? 25

=== STEP 1: SEARCHING YOUTUBE ===
✓ Found 25 videos

=== STEP 2: FILTERING VIDEOS ===
✓ 18 videos passed filters

=== STEP 3: DOWNLOADING AUDIO ===
✓ Downloaded 16/18 files

=== STEP 4: DEDUPLICATION ===
✓ Saved unique audio: python_tutorial_1.mp3
⚠️  Skipped duplicate: python_tutorial_2.mp3
✓ Saved unique audio: python_tutorial_3.mp3

=== SUMMARY ===
Original: 25 videos
After filtering: 18 videos
Downloaded: 16 files
Unique files: 15
Duplicates removed: 1
Total storage: 248.50 MB
```

## How It Works

### 1. Search & Filter
- Searches YouTube for keyword with user-specified count
- Filters videos by:
  - Keyword presence in title
  - Duration between 1-10 minutes
  - Title similarity (removes near-duplicates)

### 2. Download
- Downloads best quality audio from each video
- Converts to MP3 using FFmpeg
- Uses 5 parallel threads for efficiency
- Retries up to 3 times on failure

### 3. Duplicate Detection

**Method 1: File Hash** (Fastest)
- Compares SHA256 hash of downloaded file
- Instant detection of exact duplicates
- 100% accuracy for identical files

**Method 2: Audio Fingerprinting**
- Generates Chromaprint fingerprint
- Compares against local database
- Detects similar/remastered versions

**Method 3: AcoustID API** (Global)
- Queries AcoustID database
- Detects songs globally
- Requires API key and internet

### 4. Storage
- Unique audio files saved to `downloads/`
- Fingerprints stored in `fingerprints.json`
- Duplicates automatically deleted
- Logs saved to `logs/youtube_dedup.log`

## Input Validation

The system safely handles user input:

```python
Valid Inputs:
- Keyword: Any non-empty string (max 100 chars)
- Search count: 1-200
  - Less than 1? → Set to 1
  - More than 200? → Capped at 200
  - Non-integer? → Ask again

Examples:
"Enter keyword: " → "python tutorials"
"How many results? " → "1000" → Capped to 200
"How many results? " → "abc" → Error, try again
```

## Database Management

### View Fingerprints
```python
from database import FingerprintDatabase

db = FingerprintDatabase()
stats = db.get_stats()
print(stats)
```

### Export Fingerprints
```python
from pathlib import Path
db.export_fingerprints(Path("backup.json"))
```

### Import Fingerprints
```python
db.import_fingerprints(Path("backup.json"))
```

### Clear Database
```python
db.clear_database()  # WARNING: Irreversible
```

## Performance Optimization

- **Parallel Downloads**: 5 concurrent threads
- **Quick Hash Comparison**: O(1) for exact duplicates
- **Efficient Fingerprinting**: Only for unique files
- **Lazy API Calls**: Only calls AcoustID if needed
- **Caching**: Local database prevents reprocessing

## Error Handling

The system gracefully handles:

- ✅ Invalid user input (keyboard/number validation)
- ✅ Network errors (retry mechanism)
- ✅ Missing dependencies (helpful error messages)
- ✅ File system errors (proper exception handling)
- ✅ API errors (fallback to local detection)
- ✅ Corrupted files (skipped automatically)

## Logging

Logs are saved to `logs/youtube_dedup.log` with:
- Timestamp
- Log level (INFO, WARNING, ERROR, DEBUG)
- Module name
- Message

View logs:
```bash
# Last 50 lines
tail -n 50 logs/youtube_dedup.log

# Search logs
grep "Duplicate" logs/youtube_dedup.log
```

## Project Structure Rationale

### Single Responsibility Principle
- **main.py**: Orchestration only
- **config.py**: Configuration only
- **downloader.py**: YouTube operations only
- **filter.py**: Filtering logic only
- **fingerprint.py**: Fingerprinting only
- **database.py**: Storage operations only
- **utils.py**: Helper functions only

### Maintainability
- Clean imports and dependencies
- No circular imports
- Easy to add new features
- Easy to test individual modules
- Clear error messages for debugging

## Advanced Usage

### Custom Filters
```python
from filter import VideoFilter

filter_obj = VideoFilter()
videos = filter_obj.filter_by_duration(videos, 120, 480)  # 2-8 min
```

### Manual Fingerprint Generation
```python
from fingerprint import AudioFingerprinter
from pathlib import Path

fp = AudioFingerprinter()
audio_file = Path("downloads/song.mp3")
fingerprint = fp.generate_fingerprint(audio_file)
```

### Batch Processing
```python
from database import FingerprintDatabase

db = FingerprintDatabase()
all_fingerprints = db.get_all_fingerprints()

for video_id, data in all_fingerprints.items():
    print(f"{video_id}: {data['title']}")
```

## Troubleshooting

### FFmpeg not found
```
Make sure FFmpeg is installed and in PATH:
ffmpeg -version
```

### Chromaprint not found
```
Install Chromaprint tools for audio fingerprinting:
Windows: choco install chromaprint
macOS: brew install chromaprint
Linux: sudo apt-get install chromaprint-tools
```

### API errors
```
If AcoustID failing:
- Check API key in config.py
- Verify internet connection
- System will fallback to local detection
```

### Download failures
```
If videos won't download:
- Check internet connection
- Verify video accessibility (not region-blocked)
- Check FFmpeg installation
- Review logs: logs/youtube_dedup.log
```

## Security Notes

- ⚠️ API keys stored in config.py (not recommended for production)
- ⚠️ Respect YouTube ToS when downloading
- ✅ Local fingerprints never sent to servers
- ✅ No user data collected or transmitted
- ✅ AcoustID queries are anonymous

## Performance Metrics

Typical performance on modern hardware:

- Search: 2-5 seconds (depending on keyword)
- Download 10 videos: 30-60 seconds (depends on file size/connection)
- Fingerprinting: 2-5 seconds per file
- Duplicate detection: <1 second (hash), 2-5 seconds (fingerprint)

## Contributing

To extend the system:

1. Add new features to appropriate modules
2. Follow the single-responsibility principle
3. Add logging using `setup_logging()`
4. Update configuration in `config.py`
5. Add tests (create `tests/` directory)

## Dependencies

```
yt-dlp>=2023.0.0          # YouTube downloader
pyacoustid>=1.2.0         # Audio fingerprinting
librosa>=0.10.0           # Audio analysis (optional)
```

## License

This project is provided as-is for educational and personal use.

## Disclaimer

- This tool is for personal use only
- Respect YouTube's Terms of Service
- Respect copyright and licensing of downloaded content
- Authors are not responsible for misuse

## Support

For issues:
1. Check logs: `logs/youtube_dedup.log`
2. Verify dependencies are installed
3. Ensure FFmpeg and Chromaprint are in PATH
4. Check configuration in `config.py`

---

**Happy downloading! 🎵**
