"""Utility functions for YouTube Downloader."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Platform detection
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def supports_color() -> bool:
    """Check if the terminal supports color output."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    if IS_WINDOWS:
        try:
            import colorama

            colorama.init()
            return True
        except ImportError:
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return False
    return True


USE_COLOR = supports_color()


def colored(text: str, color: str = "") -> str:
    """Add ANSI color to text."""
    if not USE_COLOR or not color:
        return text

    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "magenta": "\033[95m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "reset": "\033[0m",
    }

    return f"{colors.get(color, '')}{text}{colors['reset']}"


def set_color_enabled(enabled: bool) -> None:
    """Enable or disable color output."""
    global USE_COLOR
    USE_COLOR = enabled


def log(log_file: Path, level: str, message: str, url: str = "") -> None:
    """Write a log entry to the log file."""
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if url:
            log_line = f"[{timestamp}] [{level:7}] {message} | {url}\n"
        else:
            log_line = f"[{timestamp}] [{level:7}] {message}\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable string."""
    if bytes_val == 0:
        return "0 B"

    size = float(bytes_val)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size:.2f} PB"


def format_duration(seconds: int) -> str:
    """Format seconds to HH:MM:SS string."""
    if not seconds or seconds < 0:
        return "00:00:00"

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    return f"{h:02d}:{m:02d}:{s:02d}"


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Sanitize filename by removing invalid characters."""
    if not name:
        return "Unknown"

    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    clean = clean.strip(". ")

    if len(clean) > max_length:
        clean = clean[:max_length]

    return clean if clean else "Unknown"


def is_playlist_url(url: str) -> bool:
    """Check if URL is a playlist URL."""
    return "list=" in url and "watch?v=" not in url.split("list=")[0][-15:]


def extract_video_id(url: str) -> str | None:
    """Extract video ID from YouTube URL."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def extract_playlist_id(url: str) -> str | None:
    """Extract playlist ID from YouTube URL."""
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def clear_line() -> None:
    """Clear the current terminal line."""
    print("\r" + " " * 100 + "\r", end="", flush=True)


def print_progress(text: str) -> None:
    """Print progress text on the same line."""
    print("\r" + text, end="", flush=True)


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if IS_WINDOWS else "clear")


def check_disk_space(path: Path, min_gb: float = 2.0) -> tuple[bool, float]:
    """Check if there's enough free disk space."""
    try:
        check_path = path
        while not check_path.exists() and check_path.parent != check_path:
            check_path = check_path.parent

        if not check_path.exists():
            return True, -1

        stat = shutil.disk_usage(check_path)
        free_gb = stat.free / (1024**3)

        return free_gb >= min_gb, free_gb
    except Exception:
        return True, -1


def run_command(cmd: list[str], timeout: int = 120) -> tuple[bool, str, str]:
    """Run a command and return the result."""
    try:
        kwargs: dict = {
            "capture_output": True,
            "text": True,
            "timeout": timeout,
        }

        if IS_WINDOWS:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(cmd, **kwargs)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except FileNotFoundError:
        return False, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return False, "", str(e)


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None


def get_default_download_path() -> Path:
    """Get the default download path for the current platform."""
    if IS_WINDOWS:
        return Path.home() / "Videos" / "YouTube"
    elif IS_MACOS:
        return Path.home() / "Movies" / "YouTube"
    else:
        return Path.home() / "Videos" / "YouTube"


def get_config_dir() -> Path:
    """Get the configuration directory for the current platform."""
    if IS_WINDOWS:
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif IS_MACOS:
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "youtube-downloader"


def parse_error_message(error_msg: str) -> str:
    """Convert technical error message to user-friendly message."""
    error_lower = error_msg.lower()

    error_map = {
        "http error 429": "Rate limited by YouTube - try again later",
        "too many requests": "Rate limited by YouTube - try again later",
        "video unavailable": "Video is private, deleted, or unavailable",
        "private video": "Video is private",
        "sign in": "Video requires login/age verification",
        "login": "Video requires login/age verification",
        "unsupported url": "Invalid YouTube URL",
        "network": "Network error - check your connection",
        "connection": "Network error - check your connection",
        "no video formats": "No downloadable formats available",
        "copyright": "Video blocked due to copyright",
        "geo": "Video not available in your region",
        "country": "Video not available in your region",
        "premium": "Video requires YouTube Premium/membership",
        "members only": "Video requires YouTube Premium/membership",
        "timeout": "Connection timed out - try again",
    }

    for key, message in error_map.items():
        if key in error_lower:
            return message
    return error_msg
