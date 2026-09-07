# Configuration Examples and Customization Guide

This file demonstrates common customization scenarios.

## Example 1: Short Videos Only (1-3 minutes)

Edit `config.py`:

```python
MIN_DURATION_SECONDS = 60      # 1 minute
MAX_DURATION_SECONDS = 180     # 3 minutes
```

## Example 2: Strict Duplicate Detection

Want to catch even slightly similar titles?

```python
TITLE_SIMILARITY_THRESHOLD = 0.80  # More strict (was 0.85)
```

Or loose detection:

```python
TITLE_SIMILARITY_THRESHOLD = 0.90  # More permissive
```

## Example 3: Higher Quality Audio

```python
AUDIO_BITRATE = "320"  # High quality (was "192")
# Or:
AUDIO_BITRATE = "128"  # Lower quality/smaller files
```

## Example 4: Faster Processing

Reduce concurrent downloads (faster in some cases):

```python
MAX_CONCURRENT_DOWNLOADS = 3  # Was 5
```

Or increase for very beefy systems:

```python
MAX_CONCURRENT_DOWNLOADS = 10  # Only if you have good bandwidth
```

## Example 5: Add Custom API Key

Register at https://acoustid.org/api and add:

```python
ACOUSTID_API_KEY = "YOUR_ACTUAL_API_KEY_HERE"
```

## Example 6: Production Setup

For server/automated processing:

```python
# Limits
MAX_SEARCH_LIMIT = 100              # More conservative
DEFAULT_SEARCH_COUNT = 20

# Performance
MAX_CONCURRENT_DOWNLOADS = 3
DOWNLOAD_TIMEOUT = 600              # Long timeout for slow connections
RETRY_ATTEMPTS = 5                  # More retries

# Quality
AUDIO_BITRATE = "192"               # Good balance
TITLE_SIMILARITY_THRESHOLD = 0.85

# Logging
LOG_LEVEL = "INFO"  # Or "DEBUG" for troubleshooting
```

## Example 7: Aggressive Download Settings

For building large libraries:

```python
MAX_SEARCH_LIMIT = 200              # Max allowed
DEFAULT_SEARCH_COUNT = 100          # Large batches
MAX_CONCURRENT_DOWNLOADS = 10       # Fast processing
RETRY_ATTEMPTS = 5                  # Persistent
DOWNLOAD_TIMEOUT = 600              # Long waits
```

## Example 8: Conservative Settings

For limited bandwidth:

```python
MAX_SEARCH_LIMIT = 50
DEFAULT_SEARCH_COUNT = 10
MAX_CONCURRENT_DOWNLOADS = 1        # One at a time
DOWNLOAD_TIMEOUT = 300
RETRY_ATTEMPTS = 2
AUDIO_BITRATE = "128"               # Small files
```

## Example 9: Music-Specific Setup

For downloading music:

```python
MIN_DURATION_SECONDS = 120          # Most songs 2 min+
MAX_DURATION_SECONDS = 600          # Up to 10 min
TITLE_SIMILARITY_THRESHOLD = 0.80   # Catch remixes/covers
AUDIO_BITRATE = "192"               # Good quality for music
FINGERPRINT_MIN_DURATION = 10       # Longer fingerprints
```

## Example 10: Podcast Setup

For downloading podcasts:

```python
MIN_DURATION_SECONDS = 600          # At least 10 min
MAX_DURATION_SECONDS = 7200         # Up to 2 hours
TITLE_SIMILARITY_THRESHOLD = 0.70   # Loose (episode numbers differ)
MAX_CONCURRENT_DOWNLOADS = 3        # Slower, careful downloads
```

## Custom Filters

To add custom filters, edit `filter.py` and add methods:

```python
def filter_by_channel(self, videos: List[Dict], channel_name: str) -> List[Dict]:
    """Filter videos by specific channel."""
    return [v for v in videos if channel_name.lower() in v.get('channel', '').lower()]

# Use in main.py
filtered = filter_obj.filter_by_channel(videos, "Corey Schafer")
```

## Custom Download Logic

To change audio quality, edit `downloader.py`:

```python
ydl_opts = {
    'format': 'bestaudio',  # Change this
    # Options:
    # 'bestaudio' - highest quality
    # 'worstaudio' - lowest quality
    # '251' - Opus audio (best compression)
    # '140' - AAC audio
    # '18/19/22' - Mixed formats
    ...
}
```

## Custom Database

To change fingerprint storage location:

```python
# In config.py
FINGERPRINTS_DB = Path.home() / "music_database" / "fingerprints.json"

# This stores fingerprints in user's home directory
```

## Custom Logging

To change log output:

```python
# In config.py
LOG_LEVEL = "DEBUG"  # More verbose
LOG_FILE = Path.home() / "youtube_dedup.log"  # Different location
```

## Advanced: Custom Similarity Algorithm

To improve duplicate detection, edit `filter.py`:

```python
def advanced_title_similarity(title1: str, title2: str) -> float:
    """Enhanced similarity using multiple metrics."""
    from difflib import SequenceMatcher
    
    cleaned1 = clean_title(title1)
    cleaned2 = clean_title(title2)
    
    # Sequence matching
    seq_ratio = SequenceMatcher(None, cleaned1, cleaned2).ratio()
    
    # Add other algorithms here
    # (e.g., Levenshtein distance, n-gram similarity)
    
    return seq_ratio
```

## Advanced: Custom Download Naming

Change how files are named:

```python
# In downloader.py, change the filename pattern:
safe_title = safe_filename(video_title)
file_path = self.download_folder / f"{safe_title}_{video_id}.{AUDIO_FORMAT}"

# To include upload date:
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d")
file_path = self.download_folder / f"{timestamp}_{safe_title}_{video_id}.{AUDIO_FORMAT}"
```

## Advanced: Multi-Keyword Search

Modify `main.py` to search multiple keywords:

```python
keywords = ["python", "javascript", "typescript"]
for keyword in keywords:
    videos = downloader.search_videos(keyword, 10)
    # Process each
```

## Environment-Specific Configs

Create different configs for different environments:

```bash
# config.py (default - development)
# config_prod.py (production)
# config_test.py (testing)
```

Then load conditionally:

```python
import os
if os.environ.get('ENV') == 'production':
    from config_prod import *
else:
    from config import *
```

## Performance Tuning

Monitor and adjust based on your system:

```python
# If downloads are slow:
MAX_CONCURRENT_DOWNLOADS = 10  # Increase

# If system is overloaded:
MAX_CONCURRENT_DOWNLOADS = 1   # Decrease

# If API rate limiting occurs:
ADD DELAY = 2  # Add delay between API calls
```

## Secure Configuration

For production, use environment variables:

```python
import os
from pathlib import Path

ACOUSTID_API_KEY = os.environ.get('ACOUSTID_API_KEY', '')
DOWNLOAD_FOLDER = Path(os.environ.get('DOWNLOAD_FOLDER', './downloads'))
```

Then set environment variables:

```bash
# Windows PowerShell
$env:ACOUSTID_API_KEY = "your_key"
$env:DOWNLOAD_FOLDER = "C:\music"

# Linux/macOS
export ACOUSTID_API_KEY="your_key"
export DOWNLOAD_FOLDER="/home/user/music"
```

## Migration Guide

### From Old Version to New

If upgrading, update your `config.py` with new settings:

```python
# New in v1.1
FINGERPRINT_MIN_DURATION = 3
AUDIO_BITRATE = "192"

# Keep existing
ACOUSTID_API_KEY = "your_key"
MAX_SEARCH_LIMIT = 200
```

---

**Need help?** Check [README.md](README.md) or [SETUP.md](SETUP.md)
