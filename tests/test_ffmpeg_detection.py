import unittest
from unittest.mock import patch

from downloader import YouTubeDownloader


class FFMpegDetectionTests(unittest.TestCase):
    @patch.object(YouTubeDownloader, "_find_executable_in_common_locations", return_value=None)
    @patch("downloader.shutil.which", return_value=None)
    def test_missing_ffmpeg_raises_clear_error(self, _mock_which, _mock_common_location):
        downloader = YouTubeDownloader()
        with self.assertRaisesRegex(RuntimeError, "FFmpeg"):
            downloader._ensure_ffmpeg_available()


if __name__ == "__main__":
    unittest.main()
