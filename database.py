"""
Database module for storing and managing audio fingerprints.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from config import FINGERPRINTS_DB
from utils import setup_logging, load_json_file, save_json_file


class FingerprintDatabase:
    """
    Manages storage and retrieval of audio fingerprints.
    """
    
    def __init__(self, db_path: Path = FINGERPRINTS_DB):
        """
        Initialize the fingerprint database.
        
        Args:
            db_path (Path): Path to fingerprints JSON file
        """
        self.db_path = db_path
        self.logger = setup_logging()
        self.data = self._load_database()
    
    def _load_database(self) -> dict:
        """
        Load database from JSON file.
        
        Returns:
            dict: Database content
        """
        data = load_json_file(self.db_path)
        
        # Initialize structure if empty
        if not data:
            data = {
                "fingerprints": {},
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            self._save_database(data)
        
        return data
    
    def _save_database(self, data: dict) -> bool:
        """
        Save database to JSON file.
        
        Args:
            data (dict): Data to save
            
        Returns:
            bool: True if successful
        """
        data["metadata"]["updated"] = datetime.now().isoformat()
        return save_json_file(self.db_path, data)
    
    def add_fingerprint(self, video_id: str, fingerprint_data: dict) -> bool:
        """
        Add a new fingerprint to the database.
        
        Args:
            video_id (str): YouTube video ID
            fingerprint_data (dict): Fingerprint data
                {
                    "title": str,
                    "duration": int,
                    "fingerprint": str,
                    "hash": str,
                    "timestamp": str
                }
        
        Returns:
            bool: True if successful
        """
        try:
            fingerprint_data["timestamp"] = datetime.now().isoformat()
            self.data["fingerprints"][video_id] = fingerprint_data
            
            # Save immediately
            success = self._save_database(self.data)
            
            if success:
                self.logger.debug(f"Added fingerprint for video {video_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error adding fingerprint: {e}")
            return False
    
    def get_fingerprint(self, video_id: str) -> Optional[dict]:
        """
        Retrieve a fingerprint by video ID.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            Optional[dict]: Fingerprint data or None
        """
        return self.data["fingerprints"].get(video_id)
    
    def fingerprint_exists(self, video_id: str) -> bool:
        """
        Check if a fingerprint exists in the database.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            bool: True if exists
        """
        return video_id in self.data["fingerprints"]
    
    def get_all_fingerprints(self) -> Dict[str, dict]:
        """
        Get all fingerprints from the database.
        
        Returns:
            Dict[str, dict]: All fingerprints
        """
        return self.data["fingerprints"].copy()
    
    def search_by_hash(self, hash_value: str) -> Optional[dict]:
        """
        Search for fingerprint by hash value.
        
        Args:
            hash_value (str): Hash value to search
            
        Returns:
            Optional[dict]: Found fingerprint or None
        """
        for video_id, fp_data in self.data["fingerprints"].items():
            if fp_data.get("hash") == hash_value:
                return {
                    "video_id": video_id,
                    "data": fp_data
                }
        
        return None
    
    def delete_fingerprint(self, video_id: str) -> bool:
        """
        Remove a fingerprint from the database.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            bool: True if successful
        """
        try:
            if video_id in self.data["fingerprints"]:
                del self.data["fingerprints"][video_id]
                success = self._save_database(self.data)
                
                if success:
                    self.logger.debug(f"Deleted fingerprint for video {video_id}")
                
                return success
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting fingerprint: {e}")
            return False
    
    def get_stats(self) -> dict:
        """
        Get database statistics.
        
        Returns:
            dict: Database stats
        """
        fingerprints = self.data["fingerprints"]
        
        return {
            "total_fingerprints": len(fingerprints),
            "created": self.data["metadata"].get("created"),
            "updated": self.data["metadata"].get("updated"),
            "database_size": self.db_path.stat().st_size if self.db_path.exists() else 0
        }
    
    def clear_database(self) -> bool:
        """
        Clear all fingerprints from the database.
        WARNING: This cannot be undone.
        
        Returns:
            bool: True if successful
        """
        try:
            self.data["fingerprints"] = {}
            success = self._save_database(self.data)
            
            if success:
                self.logger.warning("Database cleared")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error clearing database: {e}")
            return False
    
    def export_fingerprints(self, export_path: Path) -> bool:
        """
        Export fingerprints to external file.
        
        Args:
            export_path (Path): Path to export file
            
        Returns:
            bool: True if successful
        """
        try:
            return save_json_file(export_path, self.data)
        except Exception as e:
            self.logger.error(f"Error exporting fingerprints: {e}")
            return False
    
    def import_fingerprints(self, import_path: Path) -> bool:
        """
        Import fingerprints from external file.
        
        Args:
            import_path (Path): Path to import file
            
        Returns:
            bool: True if successful
        """
        try:
            if not import_path.exists():
                self.logger.error(f"Import file not found: {import_path}")
                return False
            
            imported_data = load_json_file(import_path)
            
            if not imported_data or "fingerprints" not in imported_data:
                self.logger.error("Invalid import file format")
                return False
            
            # Merge with existing data
            self.data["fingerprints"].update(imported_data["fingerprints"])
            success = self._save_database(self.data)
            
            if success:
                self.logger.info(f"Imported {len(imported_data['fingerprints'])} fingerprints")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error importing fingerprints: {e}")
            return False


if __name__ == "__main__":
    # Test database functionality
    logger = setup_logging()
    db = FingerprintDatabase()
    
    print("Testing database...")
    print(f"Database stats: {db.get_stats()}")
    
    # Add test fingerprint
    test_fp = {
        "title": "Test Song",
        "duration": 180,
        "fingerprint": "test_fingerprint_data",
        "hash": "test_hash_value"
    }
    
    db.add_fingerprint("test_video_123", test_fp)
    print(f"Added test fingerprint")
    
    # Retrieve it
    retrieved = db.get_fingerprint("test_video_123")
    print(f"Retrieved: {retrieved}")
    
    # Check if it exists
    exists = db.fingerprint_exists("test_video_123")
    print(f"Exists: {exists}")
    
    print("[OK] Database tests completed")
