"""
Configuration settings for YouTube Audio Deduplication System.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent

# Directory paths
DOWNLOAD_FOLDER = PROJECT_ROOT / "downloads"
FINGERPRINTS_DB = PROJECT_ROOT / "fingerprints.json"
LOGS_FOLDER = PROJECT_ROOT / "logs"

# Create directories if they don't exist
DOWNLOAD_FOLDER.mkdir(exist_ok=True)
LOGS_FOLDER.mkdir(exist_ok=True)

# API Configuration
ACOUSTID_API_KEY = "YOUR_ACOUSTID_API_KEY_HERE"  # Register at https://acoustid.org/api

# Limits and Thresholds
MAX_SEARCH_LIMIT = 200  # Hard cap for safety
DEFAULT_SEARCH_COUNT = 10
MIN_DURATION_SECONDS = 60  # 1 minute
MAX_DURATION_SECONDS = 420  # 10 minutes

# Similarity Threshold (0.0 to 1.0)
TITLE_SIMILARITY_THRESHOLD = 0.72

# Download Settings
MAX_CONCURRENT_DOWNLOADS = 5
DOWNLOAD_TIMEOUT = 300  # seconds
RETRY_ATTEMPTS = 3

# Audio Processing
AUDIO_FORMAT = "mp3"
AUDIO_BITRATE = "192"  # kbps

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = LOGS_FOLDER / "youtube_dedup.log"

# Audio Fingerprinting
FINGERPRINT_MIN_DURATION = 3  # seconds (minimum audio length for fingerprinting)
