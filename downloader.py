"""
YouTube video downloader module using yt-dlp.
"""

import json
import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from bootstrap import locate_executable
from config import (
    DOWNLOAD_FOLDER, MAX_CONCURRENT_DOWNLOADS,
    DOWNLOAD_TIMEOUT, RETRY_ATTEMPTS, AUDIO_FORMAT, AUDIO_BITRATE
)
from utils import setup_logging, safe_filename


class YouTubeDownloader:
    """
    Handles YouTube video searches and audio downloads using yt-dlp.
    """

    def __init__(self):
        self.logger = setup_logging()
        self.download_folder = DOWNLOAD_FOLDER
        self.download_folder.mkdir(parents=True, exist_ok=True)

        try:
            import yt_dlp
            self.yt_dlp = yt_dlp
        except ImportError:
            self.logger.error("yt-dlp not installed. Install with: pip install yt-dlp")
            raise

    # Common extractor args — tells yt-dlp to use Android API client,
    # bypassing the JS runtime requirement entirely. Top-level key, NOT inside postprocessors.
    _EXTRACTOR_ARGS = {
        'youtube': {
            'player_client': ['android'],
        }
    }

    def _ensure_ffmpeg_available(self):
        """Validate that FFmpeg and FFprobe are available and return their paths."""
        ffmpeg_path = locate_executable('ffmpeg') or shutil.which('ffmpeg') or self._find_executable_in_common_locations('ffmpeg')
        ffprobe_path = locate_executable('ffprobe') or shutil.which('ffprobe') or self._find_executable_in_common_locations('ffprobe')

        if not ffmpeg_path or not ffprobe_path:
            raise RuntimeError(
                "FFmpeg/FFprobe not found. The bootstrapper will try to install them on first run. "
                "If this issue persists, install FFmpeg from https://www.ffmpeg.org/download.html and ensure "
                "ffmpeg and ffprobe are available on PATH."
            )

        return ffmpeg_path, ffprobe_path

    def _find_executable_in_common_locations(self, executable_name: str):
        candidates = []
        if os.name == 'nt':
            candidates.extend([
                Path(r'C:\ffmpeg\bin') / f'{executable_name}.exe',
                Path(r'C:\Program Files\ffmpeg\bin') / f'{executable_name}.exe',
                Path(r'C:\Program Files (x86)\ffmpeg\bin') / f'{executable_name}.exe',
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'WinGet' / 'Packages',
            ])

            localappdata = os.environ.get('LOCALAPPDATA')
            if localappdata:
                winget_root = Path(localappdata) / 'Microsoft' / 'WinGet' / 'Packages'
                if winget_root.exists():
                    for match in winget_root.rglob(f'{executable_name}.exe'):
                        candidates.append(match)
        else:
            candidates.extend([
                Path('/opt/homebrew/bin') / executable_name,
                Path('/usr/local/bin') / executable_name,
                Path('/usr/bin') / executable_name,
            ])

        for candidate in candidates:
            if candidate and candidate.exists():
                return str(candidate)
        return None

    def search_videos(self, keyword: str, search_count: int) -> List[Dict]:
        self.logger.info(f"Searching YouTube for '{keyword}' (requesting {search_count} results)")

        try:
            ffmpeg_path, ffprobe_path = self._ensure_ffmpeg_available()
            search_query = f"ytsearch{search_count}:{keyword}"

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
                'force_generic_extractor': False,
                'extractor_args': self._EXTRACTOR_ARGS,
                'ffmpeg_location': ffmpeg_path,
                'ffprobe_location': ffprobe_path,
            }

            videos = []
            with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)

                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            videos.append({
                                'id': entry.get('id'),
                                'title': entry.get('title', 'Unknown'),
                                'duration': entry.get('duration', 0),
                                'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                                'channel': entry.get('uploader', 'Unknown'),
                                'views': entry.get('view_count', 0),
                            })

            self.logger.info(f"Found {len(videos)} videos")
            return videos

        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []

    def download_audio(self, video_url: str, video_id: str, video_title: str,
                       retry_count: int = 0) -> Optional[Path]:
        try:
            ffmpeg_path, ffprobe_path = self._ensure_ffmpeg_available()
            safe_title = safe_filename(video_title)
            file_path = self.download_folder / f"{safe_title}_{video_id}.mp3"

            if file_path.exists():
                self.logger.debug(f"File already exists: {file_path}")
                return file_path

            self.logger.info(f"Downloading: {video_title} [{video_id}]")

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': AUDIO_FORMAT,
                    'preferredquality': AUDIO_BITRATE,
                }],
                'extractor_args': self._EXTRACTOR_ARGS,
                'ffmpeg_location': ffmpeg_path,
                'ffprobe_location': ffprobe_path,
                'outtmpl': str(self.download_folder / f"{safe_title}_{video_id}"),
                'quiet': False,
                'no_warnings': False,
                'socket_timeout': DOWNLOAD_TIMEOUT,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
            }

            with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            if file_path.exists():
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                self.logger.info(f"[OK] Downloaded successfully ({file_size_mb:.2f} MB)")
                return file_path
            else:
                self.logger.warning(f"Download completed but file not found at {file_path}")
                return None

        except Exception as e:
            self.logger.error(f"Download failed for {video_id}: {str(e)[:200]}")

            if retry_count < RETRY_ATTEMPTS:
                self.logger.info(f"Retrying... (attempt {retry_count + 1}/{RETRY_ATTEMPTS})")
                return self.download_audio(video_url, video_id, video_title, retry_count + 1)

            return None

    def download_videos_parallel(self, videos: List[Dict]) -> Dict[str, Optional[Path]]:
        results = {}
        self.logger.info(f"Starting parallel downloads ({MAX_CONCURRENT_DOWNLOADS} concurrent)")

        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as executor:
            future_to_video = {
                executor.submit(
                    self.download_audio,
                    video['url'],
                    video['id'],
                    video['title']
                ): video['id']
                for video in videos
            }

            completed = 0
            for future in as_completed(future_to_video):
                video_id = future_to_video[future]
                try:
                    file_path = future.result()
                    results[video_id] = file_path
                    completed += 1
                    self.logger.debug(f"Progress: {completed}/{len(videos)} downloads completed")
                except Exception as e:
                    self.logger.error(f"Task error for {video_id}: {e}")
                    results[video_id] = None

        successful = sum(1 for v in results.values() if v is not None)
        self.logger.info(f"Download complete: {successful}/{len(videos)} successful")
        return results

    def get_video_info(self, video_url: str) -> Optional[Dict]:
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractor_args': self._EXTRACTOR_ARGS,
            }

            with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'channel': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'views': info.get('view_count'),
                    'likes': info.get('like_count'),
                    'description': info.get('description', '')[:500],
                }

        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return None

    def list_downloaded_files(self) -> List[Path]:
        return list(self.download_folder.glob(f"*.{AUDIO_FORMAT}"))


if __name__ == "__main__":
    logger = setup_logging()
    print("Testing downloader...")
    downloader = YouTubeDownloader()
    videos = downloader.search_videos("python", 5)
    print(f"Found {len(videos)} videos")
    if videos:
        print(f"First video: {videos[0]['title']}")
    print("[OK] Downloader test completed")