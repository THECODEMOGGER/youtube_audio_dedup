"""
Audio fingerprinting module using pyacoustid and Chromaprint.
Detects duplicates locally and via AcoustID API.
"""

import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging
import os

from bootstrap import locate_executable
from config import FINGERPRINT_MIN_DURATION, ACOUSTID_API_KEY
from utils import setup_logging
from database import FingerprintDatabase


class AudioFingerprinter:
    """
    Generates and manages audio fingerprints for duplicate detection.
    Uses both local comparison and AcoustID API.
    """
    
    def __init__(self):
        """Initialize the fingerprinter."""
        self.logger = setup_logging()
        self.db = FingerprintDatabase()
        
        # Try to import optional dependencies
        try:
            import acoustid
            self.acoustid = acoustid
            self.has_acoustid = True
        except ImportError:
            self.logger.warning("pyacoustid not installed. Install with: pip install pyacoustid")
            self.has_acoustid = False
        
        try:
            import librosa
            self.librosa = librosa
            self.has_librosa = True
        except ImportError:
            self.logger.warning("librosa not installed. Install with: pip install librosa")
            self.has_librosa = False
    
    def generate_file_hash(self, file_path: Path) -> str:
        """
        Generate SHA256 hash of audio file for quick duplicate comparison.
        
        Args:
            file_path (Path): Path to audio file
            
        Returns:
            str: SHA256 hash of file
        """
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error generating file hash: {e}")
            return ""
    
    def get_audio_duration(self, file_path: Path) -> Optional[float]:
        """
        Get duration of audio file in seconds.
        
        Args:
            file_path (Path): Path to audio file
            
        Returns:
            Optional[float]: Duration in seconds or None
        """
        try:
            if self.has_librosa:
                import librosa
                y, sr = librosa.load(file_path, sr=None, mono=True)
                duration = librosa.get_duration(y=y, sr=sr)
                return duration
            
            # Fallback: use ffprobe
            try:
                import subprocess
                ffprobe_cmd = locate_executable('ffprobe') or 'ffprobe'
                result = subprocess.run(
                    [ffprobe_cmd, '-v', 'error', '-show_entries', 'format=duration', 
                     '-of', 'default=noprint_wrappers=1:nokey=1:noprint_sections=1', 
                     str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return float(result.stdout.strip())
            except:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting audio duration: {e}")
            return None
    
    def generate_fingerprint(self, file_path: Path) -> Optional[str]:
        """
        Generate Chromaprint fingerprint for audio file.
        Requires pyacoustid and FFmpeg.
        
        Args:
            file_path (Path): Path to audio file
            
        Returns:
            Optional[str]: Fingerprint string or None
        """
        try:
            if not self.has_acoustid:
                self.logger.warning("Cannot generate fingerprint without pyacoustid")
                return None
            
            # Check file exists
            if not file_path.exists():
                self.logger.error(f"Audio file not found: {file_path}")
                return None
            
            # Check duration is long enough
            duration = self.get_audio_duration(file_path)
            if duration and duration < FINGERPRINT_MIN_DURATION:
                self.logger.warning(f"Audio too short for fingerprinting: {duration:.1f}s < {FINGERPRINT_MIN_DURATION}s")
                return None
            
            self.logger.debug(f"Generating fingerprint for {file_path.name}...")
            
            # Generate fingerprint using pyacoustid
            try:
                # This requires fpcalc (Chromaprint tool)
                import subprocess
                fpcalc_cmd = locate_executable('fpcalc') or 'fpcalc'
                result = subprocess.run(
                    [fpcalc_cmd, '-json', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)
                    fingerprint = data.get('fingerprint')
                    
                    if fingerprint:
                        self.logger.debug(f"Fingerprint generated successfully")
                        return fingerprint
                else:
                    self.logger.warning("fpcalc failed - Chromaprint may not be installed")
                    return None
                    
            except FileNotFoundError:
                self.logger.warning("fpcalc not found. Install Chromaprint tools.")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating fingerprint: {e}")
            return None
    
    def find_local_duplicate(self, file_hash: str) -> Optional[Dict]:
        """
        Search for duplicate by file hash in local database.
        
        Args:
            file_hash (str): File hash to search for
            
        Returns:
            Optional[Dict]: Duplicate info or None
        """
        return self.db.search_by_hash(file_hash)
    
    def query_acoustid_api(self, fingerprint: str, duration: int) -> Optional[Dict]:
        """
        Query AcoustID API for duplicate detection.
        
        Args:
            fingerprint (str): Audio fingerprint
            duration (int): Duration in seconds
            
        Returns:
            Optional[Dict]: API response or None
        """
        try:
            if not self.has_acoustid:
                self.logger.debug("Cannot query AcoustID without pyacoustid")
                return None
            
            if not ACOUSTID_API_KEY or ACOUSTID_API_KEY == "YOUR_ACOUSTID_API_KEY_HERE":
                self.logger.debug("AcoustID API key not configured")
                return None
            
            self.logger.debug("Querying AcoustID API...")
            
            # Query AcoustID
            try:
                results = self.acoustid.lookup(ACOUSTID_API_KEY, fingerprint, duration)
                
                if results and len(results) > 0:
                    self.logger.debug(f"AcoustID found {len(results)} match(es)")
                    return {
                        'status': 'found',
                        'results': results
                    }
                else:
                    return {
                        'status': 'not_found',
                        'results': []
                    }
                    
            except Exception as e:
                self.logger.warning(f"AcoustID API error: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error querying AcoustID: {e}")
            return None
    
    def store_fingerprint(self, video_id: str, file_path: Path, 
                         title: str, duration: int) -> bool:
        """
        Generate and store fingerprint for audio file.
        
        Args:
            video_id (str): YouTube video ID
            file_path (Path): Path to audio file
            title (str): Video title
            duration (int): Duration in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            # Generate hashes
            file_hash = self.generate_file_hash(file_path)
            fingerprint = self.generate_fingerprint(file_path)
            
            # Check for local duplicate
            local_dup = self.find_local_duplicate(file_hash)
            if local_dup:
                self.logger.warning(f"Local duplicate found: {local_dup['video_id']}")
                return False
            
            # Store in database
            fingerprint_data = {
                'title': title,
                'duration': duration,
                'fingerprint': fingerprint or '',
                'hash': file_hash,
                'file_path': str(file_path)
            }
            
            success = self.db.add_fingerprint(video_id, fingerprint_data)
            
            if success:
                self.logger.info(f"Fingerprint stored for {video_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error storing fingerprint: {e}")
            return False
    
    def detect_duplicates(self, file_path: Path, duration: int) -> Dict:
        """
        Comprehensive duplicate detection using multiple methods.
        
        Args:
            file_path (Path): Path to audio file
            duration (int): Duration in seconds
            
        Returns:
            Dict: Duplicate detection results
        """
        results = {
            'is_duplicate': False,
            'local_match': None,
            'acoustid_match': None,
            'confidence': 0.0
        }
        
        try:
            # Method 1: File hash comparison (fastest)
            file_hash = self.generate_file_hash(file_path)
            local_dup = self.find_local_duplicate(file_hash)
            
            if local_dup:
                results['is_duplicate'] = True
                results['local_match'] = local_dup
                results['confidence'] = 1.0  # Perfect match
                self.logger.info(f"Duplicate detected (hash match): {local_dup['video_id']}")
                return results
            
            # Method 2: Audio fingerprint comparison
            fingerprint = self.generate_fingerprint(file_path)
            
            if fingerprint:
                acoustid_result = self.query_acoustid_api(fingerprint, duration)
                
                if acoustid_result and acoustid_result['status'] == 'found':
                    results['is_duplicate'] = True
                    results['acoustid_match'] = acoustid_result['results'][0]
                    results['confidence'] = 0.95  # High confidence
                    self.logger.warning(f"Duplicate detected (fingerprint match)")
                    return results
            
            self.logger.debug("No duplicates detected")
            return results
            
        except Exception as e:
            self.logger.error(f"Error detecting duplicates: {e}")
            return results
    
    def get_fingerprint_stats(self) -> Dict:
        """
        Get statistics about stored fingerprints.
        
        Returns:
            Dict: Statistics
        """
        return self.db.get_stats()


if __name__ == "__main__":
    # Test fingerprinter
    logger = setup_logging()
    
    print("Testing fingerprinter...")
    fp = AudioFingerprinter()
    
    stats = fp.get_fingerprint_stats()
    print(f"Fingerprint DB stats: {stats}")
    
    print("[OK] Fingerprinter test completed")
