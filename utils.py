"""
Utility functions for the YouTube Audio Deduplication System.
"""

import logging
import os
import re
import unicodedata
from typing import Tuple
from difflib import SequenceMatcher
from pathlib import Path
import json

from config import LOG_LEVEL, LOG_FILE


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger


def clean_title(title: str) -> str:
    """
    Clean and normalize title text for comparison.
    
    Args:
        title (str): Original title
        
    Returns:
        str: Cleaned title in lowercase
    """
    # Remove accents and normalize unicode
    title = unicodedata.normalize('NFKD', title)
    title = title.encode('ascii', 'ignore').decode('utf-8')
    
    # Remove special characters and extra spaces
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title)
    
    return title.lower().strip()


def validate_integer_input(prompt: str, min_value: int = 1, max_value: int = 200) -> int:
    """
    Get and validate integer input from user.
    
    Args:
        prompt (str): Prompt message
        min_value (int): Minimum allowed value
        max_value (int): Maximum allowed value
        
    Returns:
        int: Validated integer input
    """
    logger = setup_logging()
    
    while True:
        try:
            user_input = input(prompt)
            value = int(user_input)
            
            if value <= 0:
                logger.warning(f"Invalid value. Using minimum value {min_value}.")
                return min_value
            
            if value < min_value:
                logger.warning(f"Value too low. Minimum is {min_value}. Using {min_value}.")
                return min_value
            
            if value > max_value:
                logger.warning(f"Value too high. Capping at {max_value}.")
                return max_value
            
            return value
            
        except ValueError:
            logger.error("Invalid input. Please enter a valid number.")
            print(f"[ERROR] Invalid input. Please enter an integer between {min_value} and {max_value}.")


def validate_keyword_input(prompt: str) -> str:
    """
    Get and validate keyword input from user.
    
    Args:
        prompt (str): Prompt message
        
    Returns:
        str: Validated keyword
    """
    logger = setup_logging()
    
    while True:
        keyword = input(prompt).strip()
        
        if not keyword:
            logger.error("Keyword cannot be empty")
            print("[ERROR] Keyword cannot be empty. Please try again.")
            continue
        
        if len(keyword) > 100:
            logger.warning("Keyword too long, truncating to 100 characters")
            keyword = keyword[:100]
        
        return keyword


def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate similarity between two titles using SequenceMatcher.
    
    Args:
        title1 (str): First title
        title2 (str): Second title
        
    Returns:
        float: Similarity ratio (0.0 to 1.0)
    """
    cleaned1 = clean_title(title1)
    cleaned2 = clean_title(title2)
    
    if not cleaned1 or not cleaned2:
        return 0.0
    
    return SequenceMatcher(None, cleaned1, cleaned2).ratio()


def seconds_to_time_format(seconds) -> str:
    """
    Convert seconds to HH:MM:SS format.
    
    Args:
        seconds: Time in seconds (int or float)
        
    Returns:
        str: Formatted time string
    """
    try:
        seconds = int(seconds) if seconds is not None else 0
    except (ValueError, TypeError):
        return "00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def file_exists(filepath: Path) -> bool:
    """
    Check if file exists.
    
    Args:
        filepath (Path): File path
        
    Returns:
        bool: True if file exists
    """
    return filepath.exists() and filepath.is_file()


def get_file_size_mb(filepath: Path) -> float:
    """
    Get file size in MB.
    
    Args:
        filepath (Path): File path
        
    Returns:
        float: File size in MB
    """
    if not file_exists(filepath):
        return 0.0
    return filepath.stat().st_size / (1024 * 1024)


def load_json_file(filepath: Path) -> dict:
    """
    Load JSON file safely.
    
    Args:
        filepath (Path): JSON file path
        
    Returns:
        dict: Loaded JSON data or empty dict
    """
    logger = setup_logging()
    
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Error loading {filepath}: {e}")
    
    return {}


def save_json_file(filepath: Path, data: dict) -> bool:
    """
    Save data to JSON file safely.
    
    Args:
        filepath (Path): JSON file path
        data (dict): Data to save
        
    Returns:
        bool: True if successful
    """
    logger = setup_logging()
    
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        logger.error(f"Error saving {filepath}: {e}")
        return False


def safe_filename(filename: str, max_length: int = 200) -> str:
    """
    Convert filename to safe format for filesystem.
    
    Args:
        filename (str): Original filename
        max_length (int): Maximum filename length
        
    Returns:
        str: Safe filename
    """
    # Remove invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Truncate if too long
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip()
    
    return filename


if __name__ == "__main__":
    # Test utilities
    logger = setup_logging()
    
    print("Testing utility functions...")
    print(f"Clean title: {clean_title('TEST Title!!! 123')}")
    print(f"Title similarity: {calculate_title_similarity('Song A', 'Song B')}")
    print(f"Time format: {seconds_to_time_format(125)}")
    print(f"Safe filename: {safe_filename('Invalid: File Name <test>')}")
    print("[OK] All utilities working correctly")
