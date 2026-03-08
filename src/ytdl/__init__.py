"""YouTube Downloader - A cross-platform YouTube video and playlist downloader."""

__version__ = "1.0.0"
__author__ = "Neshant S B"

from ytdl.config import Config, ConfigManager
from ytdl.downloader import DownloadManager

__all__ = ["Config", "ConfigManager", "DownloadManager", "__version__"]
