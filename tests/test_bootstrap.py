import unittest
from pathlib import Path

from bootstrap import parse_requirements, select_ffmpeg_asset_name, select_chromaprint_asset_name


class BootstrapTests(unittest.TestCase):
    def test_parse_requirements_reads_runtime_dependencies(self):
        requirements = parse_requirements(Path(__file__).resolve().parents[1] / 'requirements.txt')
        self.assertIn('yt-dlp', requirements)
        self.assertIn('pyacoustid', requirements)
        self.assertIn('librosa', requirements)
        self.assertNotIn('ffmpeg', requirements)

    def test_ffmpeg_asset_lookup_for_supported_platforms(self):
        self.assertIn('win64', select_ffmpeg_asset_name('Windows', 'x86_64').lower())
        self.assertIn('linux64', select_ffmpeg_asset_name('Linux', 'x86_64').lower())
        self.assertIn('macos64', select_ffmpeg_asset_name('Darwin', 'x86_64').lower())
        self.assertIn('macosarm64', select_ffmpeg_asset_name('Darwin', 'arm64').lower())

    def test_chromaprint_asset_lookup_for_supported_platforms(self):
        self.assertEqual(
            select_chromaprint_asset_name('Windows', 'x86_64'),
            'chromaprint-fpcalc-1.5.1-windows-x86_64.zip',
        )
        self.assertEqual(
            select_chromaprint_asset_name('Linux', 'x86_64'),
            'chromaprint-fpcalc-1.5.1-linux-x86_64.tar.gz',
        )
        self.assertEqual(
            select_chromaprint_asset_name('Darwin', 'arm64'),
            'chromaprint-fpcalc-1.5.1-macos-arm64.tar.gz',
        )


if __name__ == '__main__':
    unittest.main()
