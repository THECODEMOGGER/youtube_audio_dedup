"""Bootstrap the project environment before app imports and runtime work begin."""

from __future__ import annotations

import importlib.util
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent
TOOLS_DIR = PROJECT_ROOT / "tools"
FFMPEG_TOOLS_DIR = TOOLS_DIR / "ffmpeg"
CHROMAPRINT_TOOLS_DIR = TOOLS_DIR / "chromaprint"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
MIN_PYTHON_VERSION = (3, 9)


def print_status(prefix: str, message: str) -> None:
    print(f"{prefix} {message}")


def _canonical_requirement_name(requirement: str) -> str:
    cleaned = requirement.strip().split(";", 1)[0].strip()
    if not cleaned:
        return ""
    match = re.match(r"([A-Za-z0-9_.-]+)", cleaned)
    if not match:
        return cleaned
    return match.group(1)


def parse_requirements(requirements_path: Path = REQUIREMENTS_PATH) -> List[str]:
    """Return runtime requirement names from the project's requirements file."""
    requirements: List[str] = []
    if not requirements_path.exists():
        return requirements

    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name = _canonical_requirement_name(line)
        if name and name not in requirements:
            requirements.append(name)

    return requirements


def normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name.lower())


def has_internet() -> bool:
    try:
        with urllib.request.urlopen("https://pypi.org", timeout=5):
            return True
    except Exception:
        return False


def ensure_pip_bootstrapped() -> None:
    try:
        import pip  # noqa: F401
        return
    except ImportError:
        pass

    try:
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
    except Exception:
        raise RuntimeError(
            "Python packaging support is unavailable and pip could not be bootstrapped. "
            "Please install pip for this Python interpreter and run the app again."
        )


def is_package_installed(requirement: str) -> bool:
    package_name = _canonical_requirement_name(requirement)
    if not package_name:
        return True

    module_name = normalize_package_name(package_name)
    module_aliases = {
        "yt_dlp": ["yt_dlp"],
        "yt-dlp": ["yt_dlp"],
        "pyacoustid": ["acoustid"],
        "acoustid": ["acoustid"],
        "librosa": ["librosa"],
        "mutagen": ["mutagen"],
    }

    candidates = module_aliases.get(module_name, [module_name])
    for candidate in candidates:
        if importlib.util.find_spec(candidate) is not None:
            return True

    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            version(package_name)
            return True
        except PackageNotFoundError:
            pass
    except Exception:
        pass

    return False


def install_python_package(requirement: str) -> None:
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        requirement,
    ]
    ensure_pip_bootstrapped()
    subprocess.check_call(command)


def ensure_python_requirements(requirements_path: Path = REQUIREMENTS_PATH) -> None:
    print_status("[SETUP]", "Checking Python dependencies...")
    requirements = parse_requirements(requirements_path)
    if not requirements:
        print_status("[OK]", "No Python requirements found.")
        return

    for requirement in requirements:
        if is_package_installed(requirement):
            print_status("[OK]", requirement)
            continue

        if not has_internet():
            raise RuntimeError(
                f"Required Python package '{requirement}' is missing and no internet connection is available. "
                "Please connect to the internet and run python main.py again."
            )

        print_status("[INSTALL]", requirement)
        install_python_package(requirement)
        print_status("[OK]", requirement)


def _normalize_machine_name(machine: str) -> str:
    machine = (machine or "").lower()
    mapping = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "x64": "x86_64",
        "arm64": "arm64",
        "aarch64": "arm64",
        "armv8": "arm64",
    }
    return mapping.get(machine, machine)


def select_ffmpeg_asset_name(os_name: str, machine: str) -> str:
    normalized_machine = _normalize_machine_name(machine)
    os_name = (os_name or "").lower()

    if os_name.startswith("win") and normalized_machine == "x86_64":
        return "ffmpeg-master-latest-win64-gpl.zip"
    if os_name.startswith("linux") and normalized_machine == "x86_64":
        return "ffmpeg-master-latest-linux64-gpl.tar.xz"
    if os_name == "darwin" and normalized_machine == "x86_64":
        return "ffmpeg-master-latest-macos64-gpl.tar.xz"
    if os_name == "darwin" and normalized_machine == "arm64":
        return "ffmpeg-master-latest-macosarm64-gpl.tar.xz"
    raise RuntimeError(
        f"Unsupported platform for automatic FFmpeg download: {os_name} {machine}. "
        "Please install FFmpeg manually and ensure ffmpeg/ffprobe are on PATH."
    )


def select_chromaprint_asset_name(os_name: str, machine: str) -> str:
    normalized_machine = _normalize_machine_name(machine)
    os_name = (os_name or "").lower()

    if os_name.startswith("win") and normalized_machine == "x86_64":
        return "chromaprint-1.5.1-windows-x64.zip"
    if os_name.startswith("linux") and normalized_machine == "x86_64":
        return "chromaprint-1.5.1-linux-x86_64.tar.gz"
    if os_name == "darwin" and normalized_machine == "x86_64":
        return "chromaprint-1.5.1-macos-x86_64.tar.gz"
    if os_name == "darwin" and normalized_machine == "arm64":
        return "chromaprint-1.5.1-macos-arm64.tar.gz"
    raise RuntimeError(
        f"Unsupported platform for automatic Chromaprint download: {os_name} {machine}."
    )


def set_local_tool_path(tool_directory: Path) -> None:
    if not tool_directory.exists():
        return
    current_path = os.environ.get("PATH", "")
    entries = current_path.split(os.pathsep) if current_path else []
    tool_dir_str = str(tool_directory)
    if tool_dir_str not in entries:
        os.environ["PATH"] = tool_dir_str + os.pathsep + current_path


def locate_executable(executable_name: str, extra_roots: Optional[Iterable[Path]] = None) -> Optional[str]:
    resolved = shutil.which(executable_name)
    if resolved:
        return resolved

    roots: List[Path] = []
    if extra_roots:
        roots.extend(extra_roots)
    roots.extend(
        [
            PROJECT_ROOT / "tools",
            PROJECT_ROOT / "tools" / "ffmpeg",
            PROJECT_ROOT / "tools" / "chromaprint",
            PROJECT_ROOT / "tools" / "bin",
            PROJECT_ROOT / "bin",
        ]
    )

    for root in roots:
        if not root.exists():
            continue
        for candidate in [root / executable_name, root / f"{executable_name}.exe"]:
            if candidate.exists() and candidate.is_file():
                return str(candidate)
        for found in root.rglob(executable_name):
            if found.is_file():
                return str(found)
        for found in root.rglob(f"{executable_name}.exe"):
            if found.is_file():
                return str(found)

    return None


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, destination)


def _extract_archive(archive_path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(target_dir)
        return

    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, "r:*") as archive:
            archive.extractall(target_dir)
        return

    raise RuntimeError(f"Unsupported archive format for {archive_path}")


def _copy_executable(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    shutil.copy2(source, destination)
    if os.name != "nt":
        os.chmod(destination, 0o755)
    return destination


def _find_executable_inside_tree(root: Path, executable_name: str) -> Optional[Path]:
    for candidate in [root / executable_name, root / f"{executable_name}.exe"]:
        if candidate.exists() and candidate.is_file():
            return candidate
    for found in root.rglob(executable_name):
        if found.is_file():
            return found
    for found in root.rglob(f"{executable_name}.exe"):
        if found.is_file():
            return found
    return None


def ensure_ffmpeg_available() -> Tuple[str, str]:
    ffmpeg_path = locate_executable("ffmpeg", [FFMPEG_TOOLS_DIR, TOOLS_DIR])
    ffprobe_path = locate_executable("ffprobe", [FFMPEG_TOOLS_DIR, TOOLS_DIR])

    if ffmpeg_path and ffprobe_path:
        return ffmpeg_path, ffprobe_path

    if not has_internet():
        raise RuntimeError(
            "FFmpeg is missing and no internet connection is available. "
            "Please connect to the internet and run python main.py again."
        )

    os_name = platform.system()
    machine = platform.machine()
    asset_name = select_ffmpeg_asset_name(os_name, machine)
    archive_url = f"https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/{asset_name}"
    archive_path = TOOLS_DIR / asset_name
    extract_root = TOOLS_DIR / "ffmpeg_download"

    print_status("[SETUP]", "FFmpeg not found. Downloading a local build...")
    _download(archive_url, archive_path)
    if extract_root.exists():
        shutil.rmtree(extract_root)
    _extract_archive(archive_path, extract_root)

    ffmpeg_source = _find_executable_inside_tree(extract_root, "ffmpeg") or _find_executable_inside_tree(extract_root, "ffmpeg.exe")
    ffprobe_source = _find_executable_inside_tree(extract_root, "ffprobe") or _find_executable_inside_tree(extract_root, "ffprobe.exe")

    if not ffmpeg_source or not ffprobe_source:
        raise RuntimeError(
            "FFmpeg download completed but the expected ffmpeg/ffprobe executables were not found inside the archive."
        )

    final_dir = FFMPEG_TOOLS_DIR
    final_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_dest = _copy_executable(ffmpeg_source, final_dir / ffmpeg_source.name)
    ffprobe_dest = _copy_executable(ffprobe_source, final_dir / ffprobe_source.name)
    set_local_tool_path(final_dir)

    if not ffmpeg_dest.exists() or not ffprobe_dest.exists():
        raise RuntimeError("Failed to install FFmpeg binaries locally.")

    ffmpeg_path = str(ffmpeg_dest)
    ffprobe_path = str(ffprobe_dest)
    subprocess.run([ffmpeg_path, "-version"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([ffprobe_path, "-version"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print_status("[OK]", f"FFmpeg installed locally at {final_dir}")
    return ffmpeg_path, ffprobe_path


def ensure_chromaprint_available() -> Optional[str]:
    fpcalc_path = locate_executable("fpcalc", [CHROMAPRINT_TOOLS_DIR, TOOLS_DIR])
    if fpcalc_path:
        return fpcalc_path

    if not has_internet():
        print_status("[WARN]", "Chromaprint/fpcalc is missing and no internet connection is available; fingerprinting may be unavailable.")
        return None

    os_name = platform.system()
    machine = platform.machine()
    try:
        asset_name = select_chromaprint_asset_name(os_name, machine)
    except RuntimeError as exc:
        print_status("[WARN]", str(exc))
        return None

    archive_url = f"https://github.com/acoustid/chromaprint/releases/download/v1.5.1/{asset_name}"
    archive_path = TOOLS_DIR / asset_name
    extract_root = TOOLS_DIR / "chromaprint_download"

    print_status("[SETUP]", "Chromaprint/fpcalc not found. Downloading a local copy...")
    _download(archive_url, archive_path)
    if extract_root.exists():
        shutil.rmtree(extract_root)
    _extract_archive(archive_path, extract_root)

    fpcalc_source = _find_executable_inside_tree(extract_root, "fpcalc") or _find_executable_inside_tree(extract_root, "fpcalc.exe")
    if not fpcalc_source:
        print_status("[WARN]", "Chromaprint download completed but fpcalc was not found in the archive.")
        return None

    final_dir = CHROMAPRINT_TOOLS_DIR
    final_dir.mkdir(parents=True, exist_ok=True)
    fpcalc_dest = _copy_executable(fpcalc_source, final_dir / fpcalc_source.name)
    set_local_tool_path(final_dir)
    print_status("[OK]", f"Chromaprint installed locally at {final_dir}")
    return str(fpcalc_dest)


def ensure_runtime_environment() -> None:
    current_version = sys.version_info[:2]
    if current_version < MIN_PYTHON_VERSION:
        print_status(
            "[ERROR]",
            f"This project requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or newer. "
            f"Current interpreter: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}. "
            "Please upgrade Python and run the project again.",
        )
        raise SystemExit(1)

    print_status("[OK]", f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    ensure_python_requirements(REQUIREMENTS_PATH)
    ffmpeg_path, ffprobe_path = ensure_ffmpeg_available()
    if not ffmpeg_path or not ffprobe_path:
        raise RuntimeError("Unable to locate a usable FFmpeg/FFprobe installation after setup.")
    ensure_chromaprint_available()
    print_status("[SETUP]", "Environment ready.")


if __name__ == "__main__":
    try:
        ensure_runtime_environment()
    except Exception as exc:
        print_status("[ERROR]", f"Setup failed: {exc}")
        raise
