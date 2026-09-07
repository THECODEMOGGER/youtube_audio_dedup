"""
Main entry point for the YouTube Audio Deduplication System.
"""

import sys
from pathlib import Path

from utils import setup_logging, validate_keyword_input, validate_integer_input
from downloader import YouTubeDownloader
from filter import VideoFilter, print_video_list
from fingerprint import AudioFingerprinter
from database import FingerprintDatabase
from config import MAX_SEARCH_LIMIT, DEFAULT_SEARCH_COUNT, MIN_DURATION_SECONDS, MAX_DURATION_SECONDS


class YouTubeAudioDedupSystem:

    def __init__(self):
        self.logger = setup_logging()
        self.downloader = YouTubeDownloader()
        self.downloader._ensure_ffmpeg_available()
        self.filter = VideoFilter()
        self.fingerprinter = AudioFingerprinter()
        self.database = FingerprintDatabase()

        print("=" * 80)
        print("  YouTube Audio Deduplication System")
        print("=" * 80)

    # ------------------------------------------------------------------ MENU
    def show_menu(self) -> str:
        print("\n" + "=" * 80)
        print("  MENU")
        print("=" * 80)
        print("  1. Start new download session")
        print("  2. View database statistics")
        print("  3. List downloaded files")
        print("  4. Clear database")
        print("  6. Exit")
        print("  7. Download songs by artist")
        print("=" * 80)
        return input("\nSelect option: ").strip()

    # ----------------------------------------------------------- USER INPUT
    def get_user_input(self):
        keyword = validate_keyword_input("Enter search keyword: ")
        count = validate_integer_input(
            f"How many songs to download (1-{MAX_SEARCH_LIMIT}): ",
            min_value=1,
            max_value=MAX_SEARCH_LIMIT
        )
        return keyword, count

    # --------------------------------------------------------- MAIN WORKFLOW
    def run_workflow(self, keyword: str, count: int) -> bool:
        print(f"\n[START] Searching YouTube for: '{keyword}'")

        # --- Step 1: Search
        search_count = min(count * 5, MAX_SEARCH_LIMIT)
        videos = self.downloader.search_videos(keyword, search_count)

        if not videos:
            print("[ERROR] No videos found. Try a different keyword.")
            return False

        print(f"[OK] Found {len(videos)} videos")

        # --- Step 2: Filter
        print(f"\n[FILTER] Applying filters...")
        filtered = self.filter.apply_all_filters(
            videos,
            keyword,
            min_duration=MIN_DURATION_SECONDS,
            max_duration=MAX_DURATION_SECONDS
        )

        if not filtered:
            print("[ERROR] No videos passed the filters.")
            return False

        print(f"[OK] {len(filtered)} videos passed filters")
        print_video_list(filtered[:count], "Videos to download")

        # --- Step 3: Download + dedup
        print(f"\n[DOWNLOAD] Downloading up to {count} unique tracks...")

        downloaded = 0
        skipped_dupes = 0

        for video in filtered:
            if downloaded >= count:
                break

            video_id    = video.get('id', '')
            video_title = video.get('title', 'Unknown')
            video_url   = video.get('url', '')
            duration    = video.get('duration', 0) or 0

            # Skip if already fingerprinted in a previous run
            if self.database.fingerprint_exists(video_id):
                print(f"[SKIP] Already in database: {video_title}")
                skipped_dupes += 1
                continue

            print(f"\n  Downloading: {video_title}")

            file_path = self.downloader.download_audio(video_url, video_id, video_title)

            if not file_path:
                print(f"  [FAILED] Could not download: {video_title}")
                continue

            # --- Step 4: Duplicate detection
            dup_result = self.fingerprinter.detect_duplicates(file_path, int(duration))

            if dup_result.get('is_duplicate'):
                confidence = dup_result.get('confidence', 0)
                print(f"  [DUPLICATE] Detected (confidence {confidence:.0%}) - removing file")
                try:
                    file_path.unlink()
                except Exception:
                    pass
                skipped_dupes += 1
                continue

            # --- Step 5: Store fingerprint
            self.fingerprinter.store_fingerprint(video_id, file_path, video_title, int(duration))

            downloaded += 1
            size_mb = file_path.stat().st_size / (1024 * 1024) if file_path.exists() else 0
            print(f"  [OK] Saved: {file_path.name} ({size_mb:.2f} MB)")

        # --- Summary
        print("\n" + "=" * 80)
        print("  SUMMARY")
        print("=" * 80)
        print(f"  Requested  : {count}")
        print(f"  Downloaded : {downloaded}")
        print(f"  Duplicates : {skipped_dupes}")
        print("=" * 80)

        return downloaded > 0

    # ---------------------------------------------------------- ARTIST MODE
    def artist_mode(self):
        artist = validate_keyword_input("Enter artist name: ")
        count  = validate_integer_input("How many songs: ", min_value=1, max_value=50)

        print(f"\n[ARTIST] Searching for songs by: {artist}")

        queries = [
            f"{artist} official",
            f"{artist} songs",
            f"{artist} hits",
            f"{artist} best songs",
        ]

        done = 0
        for q in queries:
            if done >= count:
                break
            print(f"\n  Query: '{q}'")
            success = self.run_workflow(q, count - done)
            if success:
                done = self.database.get_stats().get('total_fingerprints', done)

        print(f"\n[DONE] Artist mode complete. Total in database: {self.database.get_stats().get('total_fingerprints', 0)}")

    # ----------------------------------------------------------- DB STATS
    def view_stats(self):
        stats = self.database.get_stats()
        print("\n" + "=" * 80)
        print("  DATABASE STATISTICS")
        print("=" * 80)
        print(f"  Total fingerprints : {stats.get('total_fingerprints', 0)}")
        print(f"  Created            : {stats.get('created', 'N/A')}")
        print(f"  Last updated       : {stats.get('updated', 'N/A')}")
        size_kb = stats.get('database_size', 0) / 1024
        print(f"  Database size      : {size_kb:.2f} KB")
        print("=" * 80)

    # ---------------------------------------------------------- LIST FILES
    def list_downloaded_files(self):
        files = self.downloader.list_downloaded_files()
        if not files:
            print("\n[NO RESULTS] No downloaded files found.")
            return
        print(f"\n[FILES] {len(files)} downloaded file(s):")
        total_mb = 0.0
        for f in files:
            size_mb = f.stat().st_size / (1024 * 1024)
            total_mb += size_mb
            print(f"  {f.name}  ({size_mb:.2f} MB)")
        print(f"\n  Total: {total_mb:.2f} MB")

    # -------------------------------------------------------- CLEAR DB
    def clear_database(self):
        confirm = input("\n[WARNING] This will DELETE all fingerprints. Type YES to confirm: ").strip()
        if confirm == "YES":
            success = self.database.clear_database()
            print("[OK] Database cleared." if success else "[ERROR] Failed to clear database.")
        else:
            print("[CANCELLED] Database was not cleared.")

    # ------------------------------------------------------- MAIN LOOP
    def main_loop(self):
        while True:
            try:
                choice = self.show_menu()

                if choice == "1":
                    keyword, count = self.get_user_input()
                    self.run_workflow(keyword, count)

                elif choice == "2":
                    self.view_stats()

                elif choice == "3":
                    self.list_downloaded_files()

                elif choice == "4":
                    self.clear_database()

                elif choice == "6":
                    print("\n[GOODBYE] Exiting. Goodbye!")
                    break

                elif choice == "7":
                    self.artist_mode()

                else:
                    print("[ERROR] Invalid option. Please choose from the menu.")

            except KeyboardInterrupt:
                print("\n\n[WARNING] Interrupted by user. Exiting.")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                print(f"[ERROR] Unexpected error: {e}")


def main():
    try:
        app = YouTubeAudioDedupSystem()
        app.main_loop()
    except Exception as e:
        print(f"[FATAL] Could not start system: {e}")
        sys.exit(1)


if __name__ == "__main__":      # <-- FIXED: was == "main"
    main()