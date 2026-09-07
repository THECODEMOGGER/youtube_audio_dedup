#!/usr/bin/env python3
"""
Example and testing script demonstrating the YouTube Audio Deduplication System API.

This script shows how to use individual modules programmatically instead of 
through the interactive menu.

Usage:
    python examples.py    # Run all examples
    python examples.py search    # Run search example only
    python examples.py filter    # Run filter example only
"""

import sys
from pathlib import Path

# Test imports
def test_imports():
    """Test that all required modules can be imported."""
    print("\n" + "="*80)
    print("  TESTING IMPORTS")
    print("="*80)
    
    try:
        print("Importing utils...", end=" ")
        from utils import setup_logging, validate_integer_input, calculate_title_similarity
        logger = setup_logging()
        print("[OK]")
        
        print("Importing config...", end=" ")
        from config import MAX_SEARCH_LIMIT, AUDIO_BITRATE
        print("[OK]")
        
        print("Importing database...", end=" ")
        from database import FingerprintDatabase
        print("[OK]")
        
        print("Importing downloader...", end=" ")
        from downloader import YouTubeDownloader
        print("[OK]")
        
        print("Importing filter...", end=" ")
        from filter import VideoFilter
        print("[OK]")
        
        print("Importing fingerprint...", end=" ")
        from fingerprint import AudioFingerprinter
        print("[OK]")
        
        print("\n[OK] All imports successful!\n")
        return True
    
    except ImportError as e:
        print(f"\n[FAILED] Import failed: {e}")
        print("Install dependencies with: pip install -r requirements.txt")
        return False


def example_filtering():
    """Example: Filter videos"""
    print("\n" + "="*80)
    print("  EXAMPLE: VIDEO FILTERING")
    print("="*80)
    
    from filter import VideoFilter, print_video_list
    
    # Create test data
    test_videos = [
        {
            'id': 'video1',
            'title': 'Python Programming Tutorial Part 1',
            'duration': 480,  # 8 minutes
            'channel': 'Code Masters',
            'views': 50000
        },
        {
            'id': 'video2',
            'title': 'Python Programming Tutorial Part 2',
            'duration': 540,  # 9 minutes
            'channel': 'Code Masters',
            'views': 45000
        },
        {
            'id': 'video3',
            'title': 'JavaScript Basics',
            'duration': 450,  # 7.5 minutes
            'channel': 'Web Dev Pro',
            'views': 60000
        },
        {
            'id': 'video4',
            'title': 'Python Quick Tips',
            'duration': 150,  # 2.5 minutes (too short)
            'channel': 'Dev Tips',
            'views': 30000
        },
        {
            'id': 'video5',
            'title': 'Learning Python Programming',
            'duration': 500,  # 8.3 minutes (similar to video1)
            'channel': 'Educational Channel',
            'views': 40000
        },
    ]
    
    print(f"\nStarting with {len(test_videos)} test videos")
    print_video_list(test_videos, "Original Videos")
    
    # Apply filters
    filter_obj = VideoFilter()
    
    # Filter 1: Keyword
    filtered_keyword = filter_obj.filter_by_keyword(test_videos, 'python')
    print(f"\nAfter keyword filter 'python': {len(filtered_keyword)} videos")
    
    # Filter 2: Duration
    filtered_duration = filter_obj.filter_by_duration(filtered_keyword, 180, 600)
    print(f"After duration filter (3-10 min): {len(filtered_duration)} videos")
    
    # Filter 3: Similarity
    filtered_similarity = filter_obj.filter_duplicates_by_title(filtered_duration, threshold=0.85)
    print(f"After similarity filter (85% threshold): {len(filtered_similarity)} videos")
    
    print_video_list(filtered_similarity, "Final Filtered Videos")
    
    print("[OK] Filtering example completed")


def example_similarity():
    """Example: Title similarity calculation"""
    print("\n" + "="*80)
    print("  EXAMPLE: TITLE SIMILARITY")
    print("="*80)
    
    from utils import calculate_title_similarity
    
    test_pairs = [
        ("Python Tutorial", "Python Programming"),
        ("Machine Learning 101", "Machine Learning Basics"),
        ("JavaScript Tips", "Python Tips"),
        ("Song Name (Cover)", "Song Name"),
        ("The Beatles Greatest Hits", "Beatles Greatest Hits"),
    ]
    
    print("\nTitle similarity scores (0.0 = different, 1.0 = identical):\n")
    print(f"{'Title 1':<40} {'Title 2':<40} {'Similarity':<12}")
    print("-" * 92)
    
    for title1, title2 in test_pairs:
        similarity = calculate_title_similarity(title1, title2)
        score_bar = "█" * int(similarity * 10) + "░" * (10 - int(similarity * 10))
        print(f"{title1:<40} {title2:<40} {similarity:.2f} {score_bar}")
    
    print("\n[OK] Similarity example completed")


def example_database():
    """Example: Fingerprint database operations"""
    print("\n" + "="*80)
    print("  EXAMPLE: FINGERPRINT DATABASE")
    print("="*80)
    
    from database import FingerprintDatabase
    from datetime import datetime
    
    # Create database instance
    db = FingerprintDatabase()
    
    # Show current stats
    stats = db.get_stats()
    print(f"\nCurrent database stats:")
    print(f"  Total fingerprints: {stats['total_fingerprints']}")
    print(f"  Database size: {stats['database_size'] / 1024:.2f} KB")
    print(f"  Created: {stats['created']}")
    print(f"  Updated: {stats['updated']}")
    
    # Add example fingerprint
    test_video_id = "example_test_123"
    test_fingerprint = {
        'title': 'Example Song for Testing',
        'duration': 300,
        'fingerprint': 'fingerprint_hash_here_abcd1234',
        'hash': 'sha256_hash_here_xyz789'
    }
    
    print(f"\nAdding example fingerprint...")
    success = db.add_fingerprint(test_video_id, test_fingerprint)
    
    if success:
        print(f"[OK] Added fingerprint for video: {test_video_id}")
        
        # Retrieve it
        retrieved = db.get_fingerprint(test_video_id)
        if retrieved:
            print(f"[OK] Retrieved fingerprint:")
            print(f"  Title: {retrieved['title']}")
            print(f"  Duration: {retrieved['duration']} seconds")
            print(f"  Added at: {retrieved['timestamp']}")
        
        # Check existence
        exists = db.fingerprint_exists(test_video_id)
        print(f"[OK] Fingerprint exists: {exists}")
        
        # Cleanup test data
        db.delete_fingerprint(test_video_id)
        print(f"[OK] Cleaned up test fingerprint")
    else:
        print("[ERROR] Failed to add fingerprint")
    
    print("\n[OK] Database example completed")


def example_youtube_search():
    """Example: Search YouTube (requires yt-dlp)"""
    print("\n" + "="*80)
    print("  EXAMPLE: YOUTUBE SEARCH")
    print("="*80)
    
    try:
        from downloader import YouTubeDownloader
        
        downloader = YouTubeDownloader()
        
        # Search for videos (small test)
        keyword = "python programming"
        count = 3
        
        print(f"\nSearching YouTube for '{keyword}' ({count} results)...")
        videos = downloader.search_videos(keyword, count)
        
        if videos:
            print(f"[OK] Found {len(videos)} videos:\n")
            print(f"{'#':<3} {'Title':<50} {'Duration':<12} {'Channel':<25}")
            print("-" * 95)
            
            for i, video in enumerate(videos, 1):
                duration_str = f"{video.get('duration', 0) // 60}m"
                title = video.get('title', 'Unknown')[:49]
                channel = video.get('channel', 'Unknown')[:24]
                print(f"{i:<3} {title:<50} {duration_str:<12} {channel:<25}")
        else:
            print("[ERROR] No videos found")
        
        print("\n[OK] YouTube search example completed")
        print("(No videos were downloaded in this example)")
    
    except Exception as e:
        print(f"Note: YouTube search requires yt-dlp and internet connection")
        print(f"Error: {e}")


def example_validation():
    """Example: Input validation"""
    print("\n" + "="*80)
    print("  EXAMPLE: INPUT VALIDATION")
    print("="*80)
    
    from utils import clean_title, safe_filename
    
    test_titles = [
        "SONG TITLE!!!  Multiple   spaces",
        "Naïve Café (Cover)",
        "Test [with] various {chars}",
        "   leading and trailing spaces   "
    ]
    
    print("\nTitle cleaning examples:\n")
    print(f"{'Original':<50} {'Cleaned':<50}")
    print("-" * 100)
    
    for title in test_titles:
        cleaned = clean_title(title)
        print(f"{title:<50} {cleaned:<50}")
    
    # Filename examples
    test_filenames = [
        "Song Title | Artist (Cover) [2020].mp3",
        "Very Very Very Very Very Very Long Filename That Exceeds Maximum Length Limit",
        "Invalid: File <Name> \"Test\".mp3"
    ]
    
    print("\n\nSafe filename examples:\n")
    print(f"{'Original':<70} {'Safe':<50}")
    print("-" * 120)
    
    for filename in test_filenames:
        safe = safe_filename(filename)
        print(f"{filename:<70} {safe:<50}")
    
    print("\n[OK] Validation example completed")


def main():
    """Run examples"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  YouTube Audio Deduplication System - Examples & API Usage".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    # Check imports first
    if not test_imports():
        return 1
    
    # Run examples
    if len(sys.argv) > 1:
        example_name = sys.argv[1].lower()
        if example_name == "search":
            example_youtube_search()
        elif example_name == "filter":
            example_filtering()
        elif example_name == "similarity":
            example_similarity()
        elif example_name == "database":
            example_database()
        elif example_name == "validation":
            example_validation()
        else:
            print(f"\nUnknown example: {example_name}")
            print("Available: search, filter, similarity, database, validation")
            return 1
    else:
        # Run all examples
        print("\nRunning all examples...\n")
        
        try:
            example_validation()
            example_similarity()
            example_filtering()
            example_database()
            example_youtube_search()
        except Exception as e:
            print(f"\n[ERROR] Error during examples: {e}")
            return 1
    
    print("\n" + "="*80)
    print("  ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nNext steps:")
    print("  1. Review the code in this file to understand the API")
    print("  2. Check documentation files for more details")
    print("  3. Run: python main.py  (to use the interactive system)")
    print("\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
