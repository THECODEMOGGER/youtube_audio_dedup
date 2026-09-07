"""
Video filtering module for keyword, duration, and title similarity checks.
"""

from typing import List, Dict
from config import (
    MIN_DURATION_SECONDS, MAX_DURATION_SECONDS,
    TITLE_SIMILARITY_THRESHOLD
)
from utils import setup_logging, calculate_title_similarity


class VideoFilter:
    def __init__(self):
        self.logger = setup_logging()
        self.blocked_keywords = [
            'remix', 'jukebox', 'full album', 'lofi', 'slowed',
            'reverb', 'cover', 'version', 'dj', 'mix'
        ]

    def _get_active_blocked_keywords(self, user_keyword: str) -> List[str]:
        """Determine which blocked keywords to apply based on user input."""
        user_keyword_lower = user_keyword.lower()
        active_blocked = []
        
        for blocked_kw in self.blocked_keywords:
            if blocked_kw not in user_keyword_lower:
                active_blocked.append(blocked_kw)
        
        return active_blocked

    # -------- FIXED KEYWORD FILTER --------
    def filter_by_keyword(self, videos: List[Dict], keyword: str) -> List[Dict]:
        """
        Filter videos by keyword in title (case-insensitive).
        Uses partial word matching.
        Also rejects videos with blocked keywords or title length > 100.
        """
        keywords = keyword.lower().split()
        active_blocked = self._get_active_blocked_keywords(keyword)
        filtered = []

        for video in videos:
            title = video.get('title', '')
            title_lower = title.lower()

            # Reject if title too long
            if len(title) > 100:
                continue

            # Reject if title contains active blocked keywords
            if any(blocked_kw in title_lower for blocked_kw in active_blocked):
                continue

            # Match if ANY word exists
            if any(word in title_lower for word in keywords):
                filtered.append(video)

        self.logger.info(f"Keyword filter: {len(videos)} -> {len(filtered)} videos")
        return filtered

    # -------- DURATION FILTER --------
    def filter_by_duration(self, videos: List[Dict],
                           min_duration: int = MIN_DURATION_SECONDS,
                           max_duration: int = MAX_DURATION_SECONDS) -> List[Dict]:

        filtered = []

        for video in videos:
            duration = video.get('duration', 0)

            if duration is None:
                continue

            try:
                duration = int(duration)
            except:
                duration = 0

            if min_duration <= duration <= max_duration:
                filtered.append(video)

        self.logger.info(f"Duration filter ({min_duration}s - {max_duration}s): {len(videos)} -> {len(filtered)} videos")
        return filtered

    # -------- TITLE DUPLICATE FILTER --------
    def filter_duplicates_by_title(self, videos: List[Dict],
                                  threshold: float = TITLE_SIMILARITY_THRESHOLD) -> List[Dict]:

        if not videos:
            return []

        unique_videos = []

        for current_video in videos:
            is_duplicate = False
            current_title = current_video.get('title', '')

            for unique_video in unique_videos:
                unique_title = unique_video.get('title', '')
                similarity = calculate_title_similarity(current_title, unique_title)

                if similarity >= threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_videos.append(current_video)

        self.logger.info(f"Title similarity filter (threshold: {threshold}): {len(videos)} -> {len(unique_videos)} videos")
        return unique_videos

    # -------- APPLY ALL --------
    def apply_all_filters(self, videos: List[Dict], keyword: str,
                         min_duration: int = MIN_DURATION_SECONDS,
                         max_duration: int = MAX_DURATION_SECONDS,
                         similarity_threshold: float = TITLE_SIMILARITY_THRESHOLD) -> List[Dict]:

        self.logger.info(f"Applying all filters to {len(videos)} videos...")

        step1 = self.filter_by_keyword(videos, keyword)
        step2 = self.filter_by_duration(step1, min_duration, max_duration)
        step3 = self.filter_duplicates_by_title(step2, similarity_threshold)

        self.logger.info(f"Final result: {len(videos)} -> {len(step3)} videos")

        return step3


# -------- PRINT FUNCTION (FIXED) --------
def print_video_list(videos: List[Dict], title: str = "Videos") -> None:

    if not videos:
        print(f"\n[NO RESULTS] No videos in {title}")
        return

    print(f"\n{'=' * 80}")
    print(f"  {title.upper()} ({len(videos)} videos)")
    print(f"{'=' * 80}")

    for i, video in enumerate(videos, 1):
        duration = video.get('duration', 0)

        if duration is None:
            duration = 0

        try:
            duration = int(duration)
        except:
            duration = 0

        minutes = duration // 60
        seconds = duration % 60

        print(f"\n{i}. {video.get('title', 'Unknown')}")
        print(f"   ID: {video.get('id')}")
        print(f"   Duration: {minutes:02d}:{seconds:02d}")
        print(f"   Channel: {video.get('channel', 'Unknown')}")
        print(f"   Views: {video.get('views', 0):,}")