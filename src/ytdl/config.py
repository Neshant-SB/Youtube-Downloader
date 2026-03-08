"""Configuration management for YouTube Downloader."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ytdl.utils import clear_screen, colored, get_default_download_path


def get_default_config() -> dict[str, Any]:
    """Get the default configuration."""
    download_path = get_default_download_path()

    return {
        "paths": {
            "video_path": str(download_path),
            "playlist_path": str(download_path / "Playlists"),
            "links_file": "youtube_links.txt",
            "temp_path": ".temp",
            "log_file": "download.log",
        },
        "download": {
            "max_retries": 3,
            "retry_delay": 5,
            "request_delay": 2,
            "max_download_rate": None,
            "format": "bv*+ba/b",
            "merge_format": "mkv",
            "continue_partial": True,
        },
        "features": {
            "embed_chapters": True,
            "sponsorblock_enabled": True,
            "sponsorblock_categories": ["sponsor", "intro", "outro", "selfpromo"],
            "skip_existing": True,
            "remove_completed_links": True,
            "use_colors": True,
        },
        "limits": {
            "min_disk_space_gb": 2.0,
            "max_filename_length": 200,
            "command_timeout": 120,
        },
        "video_extensions": [".mkv", ".mp4", ".webm", ".avi", ".mov", ".flv", ".m4v"],
        "quality": {
            "prefer_quality": "best",
            "max_resolution": None,
            "max_filesize": None,
            "prefer_free_formats": False,
        },
        "metadata": {
            "embed_thumbnail": True,
            "embed_metadata": True,
            "embed_subtitles": False,
            "subtitle_languages": ["en"],
            "auto_subtitles": False,
        },
        "advanced": {
            "user_agent": None,
            "proxy": None,
            "geo_bypass": False,
            "age_limit": None,
            "cookies_file": None,
        },
    }


CONFIG_DESCRIPTIONS = {
    "paths": {
        "_desc": "File system paths",
        "video_path": "Where individual videos are saved",
        "playlist_path": "Where playlists are saved",
        "links_file": "File containing YouTube URLs",
        "temp_path": "Temporary download directory",
        "log_file": "Download log file location",
    },
    "download": {
        "_desc": "Download settings",
        "max_retries": "Number of retry attempts for failed downloads",
        "retry_delay": "Seconds to wait before retry",
        "request_delay": "Seconds between downloads (avoid rate limiting)",
        "max_download_rate": "Bandwidth limit (e.g., '5M', '500K', null for unlimited)",
        "format": "yt-dlp format selector (e.g., 'bv*+ba/b')",
        "merge_format": "Output container format (mkv, mp4, webm)",
        "continue_partial": "Resume incomplete downloads",
    },
    "features": {
        "_desc": "Feature toggles",
        "embed_chapters": "Add chapter markers if available",
        "sponsorblock_enabled": "Mark sponsored segments using SponsorBlock",
        "sponsorblock_categories": "Which segments to mark",
        "skip_existing": "Skip already downloaded videos",
        "remove_completed_links": "Remove URLs from links file after download",
        "use_colors": "Enable colored terminal output",
    },
    "limits": {
        "_desc": "Resource limits",
        "min_disk_space_gb": "Minimum free disk space required (GB)",
        "max_filename_length": "Maximum characters in filename",
        "command_timeout": "Timeout for yt-dlp commands (seconds)",
    },
    "video_extensions": {
        "_desc": "Video file extensions to recognize",
    },
    "quality": {
        "_desc": "Quality settings",
        "prefer_quality": "Quality preference (best/worst)",
        "max_resolution": "Maximum resolution (2160/1080/720, null for unlimited)",
        "max_filesize": "Maximum file size (e.g., '500M', '1G', null)",
        "prefer_free_formats": "Prefer open formats (VP9/AV1 over H.264)",
    },
    "metadata": {
        "_desc": "Metadata embedding",
        "embed_thumbnail": "Embed video thumbnail",
        "embed_metadata": "Embed title, description, etc.",
        "embed_subtitles": "Download and embed subtitles",
        "subtitle_languages": "Subtitle languages to download",
        "auto_subtitles": "Include auto-generated subtitles",
    },
    "advanced": {
        "_desc": "Advanced options",
        "user_agent": "Custom user agent string",
        "proxy": "Proxy server (e.g., 'http://proxy:8080')",
        "geo_bypass": "Bypass geographic restrictions",
        "age_limit": "Skip videos with higher age rating",
        "cookies_file": "Cookie file for authentication",
    },
}


PRESETS: dict[str, dict[str, Any]] = {
    "basic": {
        "name": "Basic Setup",
        "desc": "Simple configuration for most users",
        "changes": {
            "download.max_retries": 3,
            "download.request_delay": 2,
            "features.skip_existing": True,
            "features.remove_completed_links": True,
            "features.sponsorblock_enabled": True,
        },
    },
    "quality": {
        "name": "Maximum Quality",
        "desc": "Best quality, no limits",
        "changes": {
            "quality.max_resolution": None,
            "quality.max_filesize": None,
            "download.format": "bv*+ba/b",
            "metadata.embed_thumbnail": True,
            "metadata.embed_metadata": True,
        },
    },
    "limited": {
        "name": "Limited Bandwidth & Quality",
        "desc": "720p max, 5MB/s bandwidth limit",
        "changes": {
            "download.max_download_rate": "5M",
            "quality.max_resolution": 720,
            "quality.max_filesize": "500M",
        },
    },
    "archive": {
        "name": "Archive Mode",
        "desc": "Keep everything, full metadata",
        "changes": {
            "features.sponsorblock_enabled": False,
            "features.remove_completed_links": False,
            "metadata.embed_thumbnail": True,
            "metadata.embed_metadata": True,
            "metadata.embed_subtitles": True,
            "metadata.auto_subtitles": True,
        },
    },
    "space-saving": {
        "name": "Space Saving",
        "desc": "Minimal size, lower quality",
        "changes": {
            "quality.max_resolution": 480,
            "quality.max_filesize": "200M",
            "quality.prefer_free_formats": True,
            "metadata.embed_thumbnail": False,
            "metadata.embed_subtitles": False,
        },
    },
}


@dataclass
class Config:
    """Configuration container."""

    # Paths
    video_path: Path = field(default_factory=get_default_download_path)
    playlist_path: Path = field(default_factory=lambda: get_default_download_path() / "Playlists")
    links_file: Path = field(default_factory=lambda: Path("youtube_links.txt"))
    temp_path: Path = field(default_factory=lambda: Path(".temp"))
    log_file: Path = field(default_factory=lambda: Path("download.log"))

    # Download
    max_retries: int = 3
    retry_delay: int = 5
    request_delay: int = 2
    max_download_rate: str | None = None
    format: str = "bv*+ba/b"
    merge_format: str = "mkv"
    continue_partial: bool = True

    # Features
    embed_chapters: bool = True
    sponsorblock_enabled: bool = True
    sponsorblock_categories: list[str] = field(
        default_factory=lambda: ["sponsor", "intro", "outro", "selfpromo"]
    )
    skip_existing: bool = True
    remove_completed_links: bool = True
    use_colors: bool = True

    # Limits
    min_disk_space_gb: float = 2.0
    max_filename_length: int = 200
    command_timeout: int = 120

    # Video extensions
    video_extensions: list[str] = field(
        default_factory=lambda: [".mkv", ".mp4", ".webm", ".avi", ".mov", ".flv", ".m4v"]
    )

    # Quality
    prefer_quality: str = "best"
    max_resolution: int | None = None
    max_filesize: str | None = None
    prefer_free_formats: bool = False

    # Metadata
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    embed_subtitles: bool = False
    subtitle_languages: list[str] = field(default_factory=lambda: ["en"])
    auto_subtitles: bool = False

    # Advanced
    user_agent: str | None = None
    proxy: str | None = None
    geo_bypass: bool = False
    age_limit: int | None = None
    cookies_file: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create Config from dictionary."""
        config = cls()

        if "paths" in data:
            paths = data["paths"]
            config.video_path = Path(paths.get("video_path", config.video_path))
            config.playlist_path = Path(paths.get("playlist_path", config.playlist_path))
            config.links_file = Path(paths.get("links_file", config.links_file))
            config.temp_path = Path(paths.get("temp_path", config.temp_path))
            config.log_file = Path(paths.get("log_file", config.log_file))

        if "download" in data:
            dl = data["download"]
            config.max_retries = dl.get("max_retries", config.max_retries)
            config.retry_delay = dl.get("retry_delay", config.retry_delay)
            config.request_delay = dl.get("request_delay", config.request_delay)
            config.max_download_rate = dl.get("max_download_rate", config.max_download_rate)
            config.format = dl.get("format", config.format)
            config.merge_format = dl.get("merge_format", config.merge_format)
            config.continue_partial = dl.get("continue_partial", config.continue_partial)

        if "features" in data:
            feat = data["features"]
            config.embed_chapters = feat.get("embed_chapters", config.embed_chapters)
            config.sponsorblock_enabled = feat.get(
                "sponsorblock_enabled", config.sponsorblock_enabled
            )
            config.sponsorblock_categories = feat.get(
                "sponsorblock_categories", config.sponsorblock_categories
            )
            config.skip_existing = feat.get("skip_existing", config.skip_existing)
            config.remove_completed_links = feat.get(
                "remove_completed_links", config.remove_completed_links
            )
            config.use_colors = feat.get("use_colors", config.use_colors)

        if "limits" in data:
            lim = data["limits"]
            config.min_disk_space_gb = lim.get("min_disk_space_gb", config.min_disk_space_gb)
            config.max_filename_length = lim.get("max_filename_length", config.max_filename_length)
            config.command_timeout = lim.get("command_timeout", config.command_timeout)

        if "video_extensions" in data:
            config.video_extensions = data["video_extensions"]

        if "quality" in data:
            qual = data["quality"]
            config.prefer_quality = qual.get("prefer_quality", config.prefer_quality)
            config.max_resolution = qual.get("max_resolution", config.max_resolution)
            config.max_filesize = qual.get("max_filesize", config.max_filesize)
            config.prefer_free_formats = qual.get("prefer_free_formats", config.prefer_free_formats)

        if "metadata" in data:
            meta = data["metadata"]
            config.embed_thumbnail = meta.get("embed_thumbnail", config.embed_thumbnail)
            config.embed_metadata = meta.get("embed_metadata", config.embed_metadata)
            config.embed_subtitles = meta.get("embed_subtitles", config.embed_subtitles)
            config.subtitle_languages = meta.get("subtitle_languages", config.subtitle_languages)
            config.auto_subtitles = meta.get("auto_subtitles", config.auto_subtitles)

        if "advanced" in data:
            adv = data["advanced"]
            config.user_agent = adv.get("user_agent", config.user_agent)
            config.proxy = adv.get("proxy", config.proxy)
            config.geo_bypass = adv.get("geo_bypass", config.geo_bypass)
            config.age_limit = adv.get("age_limit", config.age_limit)
            config.cookies_file = adv.get("cookies_file", config.cookies_file)

        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert Config to dictionary."""
        return {
            "paths": {
                "video_path": str(self.video_path),
                "playlist_path": str(self.playlist_path),
                "links_file": str(self.links_file),
                "temp_path": str(self.temp_path),
                "log_file": str(self.log_file),
            },
            "download": {
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay,
                "request_delay": self.request_delay,
                "max_download_rate": self.max_download_rate,
                "format": self.format,
                "merge_format": self.merge_format,
                "continue_partial": self.continue_partial,
            },
            "features": {
                "embed_chapters": self.embed_chapters,
                "sponsorblock_enabled": self.sponsorblock_enabled,
                "sponsorblock_categories": self.sponsorblock_categories,
                "skip_existing": self.skip_existing,
                "remove_completed_links": self.remove_completed_links,
                "use_colors": self.use_colors,
            },
            "limits": {
                "min_disk_space_gb": self.min_disk_space_gb,
                "max_filename_length": self.max_filename_length,
                "command_timeout": self.command_timeout,
            },
            "video_extensions": self.video_extensions,
            "quality": {
                "prefer_quality": self.prefer_quality,
                "max_resolution": self.max_resolution,
                "max_filesize": self.max_filesize,
                "prefer_free_formats": self.prefer_free_formats,
            },
            "metadata": {
                "embed_thumbnail": self.embed_thumbnail,
                "embed_metadata": self.embed_metadata,
                "embed_subtitles": self.embed_subtitles,
                "subtitle_languages": self.subtitle_languages,
                "auto_subtitles": self.auto_subtitles,
            },
            "advanced": {
                "user_agent": self.user_agent,
                "proxy": self.proxy,
                "geo_bypass": self.geo_bypass,
                "age_limit": self.age_limit,
                "cookies_file": self.cookies_file,
            },
        }


class ConfigManager:
    """Manage configuration file operations."""

    def __init__(self, config_file: Path | None = None):
        """Initialize ConfigManager."""
        self.config_file = config_file or Path("config.json")
        self._config: Config | None = None

    @property
    def config(self) -> Config:
        """Get the current configuration."""
        if self._config is None:
            self._config = self.load()
        return self._config

    def load(self) -> Config:
        """Load configuration from file."""
        if not self.config_file.exists():
            return Config()

        try:
            with open(self.config_file, encoding="utf-8") as f:
                data = json.load(f)
            return Config.from_dict(data)
        except Exception as e:
            print(colored(f"Error loading config: {e}", "red"))
            return Config()

    def save(self, config: Config | None = None) -> bool:
        """Save configuration to file."""
        if config is None:
            config = self._config
        if config is None:
            return False

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=4)
            self._config = config
            return True
        except Exception as e:
            print(colored(f"Error saving config: {e}", "red"))
            return False

    def create_default(self) -> bool:
        """Create default configuration file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(get_default_config(), f, indent=4)
            print(colored(f"✓ Created config: {self.config_file}", "green"))
            return True
        except Exception as e:
            print(colored(f"✗ Error creating config: {e}", "red"))
            return False

    def backup(self) -> Path | None:
        """Create a backup of the current config file."""
        if not self.config_file.exists():
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.config_file.parent / f"config.backup.{timestamp}.json"

            with open(self.config_file, encoding="utf-8") as f:
                data = json.load(f)

            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            return backup_file
        except Exception:
            return None

    def reset(self) -> bool:
        """Reset configuration to defaults."""
        self.backup()
        self._config = Config()
        return self.save()

    def get_value(self, path: str) -> Any:
        """Get a configuration value using dot notation."""
        parts = path.split(".")
        data = self.config.to_dict()

        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return None
        return data

    def set_value(self, path: str, value: Any) -> bool:
        """Set a configuration value using dot notation."""
        parts = path.split(".")
        data = self.config.to_dict()

        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        key = parts[-1]
        old_value = current.get(key)

        if old_value is not None and isinstance(value, str):
            if isinstance(old_value, bool):
                value = value.lower() in ("true", "yes", "1", "on")
            elif isinstance(old_value, int):
                value = int(value)
            elif isinstance(old_value, float):
                value = float(value)
            elif isinstance(old_value, list):
                try:
                    import ast

                    value = ast.literal_eval(value)
                except Exception:
                    value = [v.strip() for v in value.split(",")]
            elif value.lower() in ("null", "none"):
                value = None

        current[key] = value
        self._config = Config.from_dict(data)
        return self.save()

    def apply_preset(self, preset_name: str) -> bool:
        """Apply a preset configuration."""
        if preset_name not in PRESETS:
            return False

        preset = PRESETS[preset_name]
        self.backup()

        for path, value in preset["changes"].items():
            self.set_value(path, value)
        return True

    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []
        config = self.config

        if config.min_disk_space_gb < 0:
            issues.append("min_disk_space_gb cannot be negative")
        if config.max_retries < 0:
            issues.append("max_retries cannot be negative")
        if config.retry_delay < 0:
            issues.append("retry_delay cannot be negative")
        if not config.format:
            issues.append("download format cannot be empty")

        return issues

    @staticmethod
    def display_value(value: Any) -> str:
        """Format value for display."""
        if value is None:
            return colored("null", "dim")
        elif isinstance(value, bool):
            return colored(str(value).lower(), "cyan")
        elif isinstance(value, (int, float)):
            return colored(str(value), "yellow")
        elif isinstance(value, list):
            return colored(str(value), "magenta")
        else:
            return colored(f'"{value}"', "green")

    def display_section(self, section: str) -> None:
        """Display a configuration section."""
        data = self.config.to_dict()

        if section not in data:
            print(colored(f"Section '{section}' not found", "red"))
            return

        section_desc = CONFIG_DESCRIPTIONS.get(section, {}).get("_desc", section)
        print(colored(f"\n[{section.upper()}] - {section_desc}", "bold"))
        print(colored("-" * 70, "dim"))

        items = data[section]
        if isinstance(items, dict):
            for key, value in items.items():
                desc = CONFIG_DESCRIPTIONS.get(section, {}).get(key, "")
                value_str = self.display_value(value)
                print(f"  {colored(key, 'cyan'):40} = {value_str}")
                if desc:
                    print(f"  {colored('↳', 'dim')} {colored(desc, 'dim')}")
        else:
            print(f"  {self.display_value(items)}")
        print()

    def display_all(self) -> None:
        """Display entire configuration."""
        for section in self.config.to_dict().keys():
            self.display_section(section)

    @staticmethod
    def display_presets() -> None:
        """Display available presets."""
        print(colored("\nAvailable Presets:", "bold"))
        print(colored("-" * 70, "dim"))

        for key, preset in PRESETS.items():
            print(f"\n  {colored(key, 'cyan'):20} - {colored(preset['name'], 'bold')}")
            print(f"  {colored('↳', 'dim')} {colored(preset['desc'], 'dim')}")
        print()

    def interactive_menu(self) -> None:
        """Run interactive configuration menu."""
        while True:
            clear_screen()
            print()
            print(colored("=" * 70, "bold"))
            print(colored("YouTube Downloader - Configuration Manager", "bold"))
            print(colored("=" * 70, "bold"))
            print()

            if not self.config_file.exists():
                print(colored("⚠ No configuration file found", "yellow"))
                print()

            print("1. View configuration")
            print("2. Edit setting")
            print("3. Apply preset")
            print("4. Reset to defaults")
            print("5. Export/Import/Backup")
            print("6. Validate configuration")
            print("0. Exit")

            choice = input(colored("\nChoice: ", "cyan")).strip()

            if choice == "0":
                print(colored("\nGoodbye!", "green"))
                break
            elif choice == "1":
                self._menu_view()
            elif choice == "2":
                self._menu_edit()
            elif choice == "3":
                self._menu_preset()
            elif choice == "4":
                self._menu_reset()
            elif choice == "5":
                self._menu_export_import()
            elif choice == "6":
                self._menu_validate()
            else:
                print(colored("Invalid choice", "red"))
                input(colored("\nPress Enter to continue...", "dim"))

    def _menu_view(self) -> None:
        """View configuration menu."""
        print(colored("\nView Configuration", "bold"))
        print(colored("-" * 70, "dim"))
        print("\n1. View all")
        print("2. View paths")
        print("3. View download settings")
        print("4. View features")
        print("5. View limits")
        print("6. View quality")
        print("7. View metadata")
        print("8. View advanced")
        print("0. Back")

        choice = input(colored("\nChoice: ", "cyan")).strip()

        sections = {
            "2": "paths",
            "3": "download",
            "4": "features",
            "5": "limits",
            "6": "quality",
            "7": "metadata",
            "8": "advanced",
        }

        if choice == "0":
            return
        elif choice == "1":
            self.display_all()
        elif choice in sections:
            self.display_section(sections[choice])

        input(colored("\nPress Enter to continue...", "dim"))

    def _menu_edit(self) -> None:
        """Edit configuration menu."""
        print(colored("\nEdit Configuration", "bold"))
        print(colored("-" * 70, "dim"))
        print("\nEnter setting path (e.g., 'download.max_retries')")
        print("Or 'list' to see all options, '0' to cancel")

        while True:
            path = input(colored("\nSetting: ", "cyan")).strip()

            if path == "0":
                return
            if path.lower() == "list":
                self.display_all()
                continue
            if not path:
                continue

            current_value = self.get_value(path)

            if current_value is None:
                print(colored(f"Setting '{path}' not found", "red"))
                continue

            print(f"Current value: {self.display_value(current_value)}")

            parts = path.split(".")
            if len(parts) == 2:
                desc = CONFIG_DESCRIPTIONS.get(parts[0], {}).get(parts[1], "")
                if desc:
                    print(colored(f"↳ {desc}", "dim"))

            new_value = input(colored("New value (or empty to cancel): ", "yellow")).strip()

            if not new_value:
                continue

            if self.set_value(path, new_value):
                print(colored("✓ Configuration updated", "green"))
                break
            else:
                print(colored("✗ Failed to update setting", "red"))

    def _menu_preset(self) -> None:
        """Apply preset menu."""
        self.display_presets()

        print("0. Cancel")
        preset_key = input(colored("\nSelect preset: ", "cyan")).strip()

        if preset_key == "0":
            return

        if preset_key not in PRESETS:
            print(colored("Invalid preset", "red"))
            input(colored("\nPress Enter to continue...", "dim"))
            return

        preset = PRESETS[preset_key]

        print(colored(f"\nApplying preset: {preset['name']}", "bold"))
        print(colored(preset["desc"], "dim"))

        confirm = input(colored("\nConfirm? (yes/no): ", "yellow")).strip().lower()

        if confirm not in ("yes", "y"):
            print(colored("Cancelled", "yellow"))
            input(colored("\nPress Enter to continue...", "dim"))
            return

        if self.apply_preset(preset_key):
            for path, value in preset["changes"].items():
                print(colored(f"  ✓ Set {path} = {value}", "green"))
            print(colored("\n✓ Preset applied successfully", "green"))
        else:
            print(colored("\n✗ Failed to apply preset", "red"))

        input(colored("\nPress Enter to continue...", "dim"))

    def _menu_reset(self) -> None:
        """Reset configuration menu."""
        print(colored("\nReset Configuration", "bold"))
        print(colored("-" * 70, "dim"))
        print(colored("\n⚠ This will reset ALL settings to defaults!", "yellow"))

        confirm = input(colored("\nType 'RESET' to confirm: ", "red")).strip()

        if confirm != "RESET":
            print(colored("Cancelled", "yellow"))
            input(colored("\nPress Enter to continue...", "dim"))
            return

        if self.reset():
            print(colored("✓ Configuration reset to defaults", "green"))

        input(colored("\nPress Enter to continue...", "dim"))

    def _menu_export_import(self) -> None:
        """Export/Import menu."""
        print(colored("\nExport/Import Configuration", "bold"))
        print(colored("-" * 70, "dim"))
        print("\n1. Export to file")
        print("2. Import from file")
        print("3. Create backup")
        print("0. Back")

        choice = input(colored("\nChoice: ", "cyan")).strip()

        if choice == "1":
            export_file = input(
                colored("\nExport to (default: config_export.json): ", "cyan")
            ).strip()
            if not export_file:
                export_file = "config_export.json"

            try:
                with open(export_file, "w", encoding="utf-8") as f:
                    json.dump(self.config.to_dict(), f, indent=4)
                print(colored(f"✓ Exported to {export_file}", "green"))
            except Exception as e:
                print(colored(f"✗ Error: {e}", "red"))

        elif choice == "2":
            import_file = input(colored("\nImport from: ", "cyan")).strip()
            if not import_file or not Path(import_file).exists():
                print(colored("File not found", "red"))
            else:
                try:
                    with open(import_file, encoding="utf-8") as f:
                        data = json.load(f)

                    self.backup()
                    self._config = Config.from_dict(data)

                    if self.save():
                        print(colored("✓ Configuration imported", "green"))
                    else:
                        print(colored("✗ Failed to save", "red"))
                except Exception as e:
                    print(colored(f"✗ Error: {e}", "red"))

        elif choice == "3":
            backup_path = self.backup()
            if backup_path:
                print(colored(f"✓ Backup created: {backup_path}", "green"))
            else:
                print(colored("✗ Failed to create backup", "red"))

        input(colored("\nPress Enter to continue...", "dim"))

    def _menu_validate(self) -> None:
        """Validate configuration menu."""
        print(colored("\nValidate Configuration", "bold"))
        print(colored("-" * 70, "dim"))

        issues = self.validate()

        if issues:
            print(colored("\n⚠ Issues found:", "yellow"))
            for issue in issues:
                print(colored(f"  • {issue}", "red"))
        else:
            print(colored("\n✓ Configuration is valid", "green"))

        input(colored("\nPress Enter to continue...", "dim"))
