# YouTube Downloader

[![CI](https://github.com/Neshant-SB/youtube-downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/Neshant-SB/youtube-downloader/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A feature-rich, cross-platform YouTube video and playlist downloader with real-time progress tracking, automatic duplicate detection, and extensive configuration options.

## ✨ Features

- 🎥 **Download Individual Videos & Playlists** - Support for single videos and complete playlists
- 🔄 **Smart Duplicate Detection** - Automatically skip already downloaded videos
- 📊 **Real-time Progress Tracking** - Live download progress with speed and ETA
- 🎯 **SponsorBlock Integration** - Mark sponsored segments automatically
- 🖼️ **Rich Metadata** - Embed thumbnails, chapters, and video information
- 📝 **Subtitle Support** - Download and embed subtitles in multiple languages
- 🚦 **Bandwidth Control** - Limit download speed to avoid network congestion
- 💾 **Disk Space Management** - Check available space before downloading
- ♻️ **Resume Downloads** - Continue interrupted downloads automatically
- 🎨 **Colored Output** - Beautiful, easy-to-read terminal interface
- ⚙️ **Interactive Configuration** - Manage settings through CLI or interactive menu
- 🎛️ **Preset Configurations** - Quick setup with predefined quality/size presets
- 🔁 **Automatic Retry** - Retry failed downloads with exponential backoff
- 🌐 **Cross-platform** - Works on Windows, macOS, and Linux

## 📋 Requirements

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** - Fast Python package installer
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - YouTube downloader (auto-installed)
- **[ffmpeg](https://ffmpeg.org/)** - For merging video and audio

## 🚀 Quick Start

### 1. Install Prerequisites

#### Install uv

**Linux/macOS:**

    curl -LsSf https://astral.sh/uv/install.sh | sh

**Windows (PowerShell):**

    irm https://astral.sh/uv/install.ps1 | iex

#### Install ffmpeg

**macOS:**

    brew install ffmpeg

**Windows:**

    scoop install ffmpeg
    # or
    choco install ffmpeg

**Linux (Debian/Ubuntu):**

    sudo apt update && sudo apt install ffmpeg

**Linux (Fedora):**

    sudo dnf install ffmpeg

**Linux (Arch):**

    sudo pacman -S ffmpeg

### 2. Clone & Setup

    git clone https://github.com/Neshant-SB/youtube-downloader.git
    cd youtube-downloader
    uv sync

### 3. Add URLs

Edit `youtube_links.txt` and add YouTube URLs (one per line):

    https://www.youtube.com/watch?v=dQw4w9WgXcQ
    https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxx

### 4. Run

**Windows:**

    run.bat

**macOS/Linux:**

    chmod +x run.sh
    ./run.sh

**Or directly:**

    uv run python main.py

## 📖 Usage

### Basic Commands

    # Start downloading
    uv run python main.py

    # Show help
    uv run python main.py --help

    # Show version
    uv run python main.py --version

### Configuration Commands

    # Interactive configuration menu
    uv run python main.py config

    # View all configuration
    uv run python main.py config view

    # View specific section
    uv run python main.py config view download

    # Get a specific value
    uv run python main.py config get download.max_retries

    # Set a value
    uv run python main.py config set download.max_retries 5
    uv run python main.py config set download.max_download_rate "5M"
    uv run python main.py config set quality.max_resolution 1080

    # Apply a preset configuration
    uv run python main.py config preset quality

    # Reset to defaults
    uv run python main.py config reset

    # Create backup
    uv run python main.py config backup

    # Validate configuration
    uv run python main.py config validate

## ⚙️ Configuration

### Configuration File

The configuration is stored in `config.json`. You can edit it directly or use the interactive menu.

### Configuration Sections

#### Paths

    {
      "paths": {
        "video_path": "~/Videos/YouTube",
        "playlist_path": "~/Videos/YouTube/Playlists",
        "links_file": "youtube_links.txt",
        "temp_path": ".temp",
        "log_file": "download.log"
      }
    }

#### Download Settings

    {
      "download": {
        "max_retries": 3,
        "retry_delay": 5,
        "request_delay": 2,
        "max_download_rate": null,
        "format": "bv*+ba/b",
        "merge_format": "mkv",
        "continue_partial": true
      }
    }

#### Features

    {
      "features": {
        "embed_chapters": true,
        "sponsorblock_enabled": true,
        "sponsorblock_categories": ["sponsor", "intro", "outro", "selfpromo"],
        "skip_existing": true,
        "remove_completed_links": true,
        "use_colors": true
      }
    }

#### Quality Settings

    {
      "quality": {
        "prefer_quality": "best",
        "max_resolution": null,
        "max_filesize": null,
        "prefer_free_formats": false
      }
    }

#### Metadata

    {
      "metadata": {
        "embed_thumbnail": true,
        "embed_metadata": true,
        "embed_subtitles": false,
        "subtitle_languages": ["en"],
        "auto_subtitles": false
      }
    }

### Preset Configurations

Apply quick configurations for common use cases:

    uv run python main.py config preset <preset-name>

| Preset | Description | Settings |
|--------|-------------|----------|
| **basic** | Simple setup for most users | Skip existing, remove completed links |
| **quality** | Maximum quality downloads | Best quality, no limits, all metadata |
| **limited** | Bandwidth & quality limits | 720p max, 5MB/s limit, 500MB max file |
| **archive** | Full archival mode | All metadata, subtitles, keep all files |
| **space-saving** | Minimize file size | 480p, 200MB limit, no thumbnails |

### Configuration Examples

#### Limit Bandwidth to 5MB/s

    uv run python main.py config set download.max_download_rate "5M"

#### Download at Maximum 720p

    uv run python main.py config set quality.max_resolution 720

#### Enable Subtitle Downloads

    uv run python main.py config set metadata.embed_subtitles true
    uv run python main.py config set metadata.subtitle_languages '["en","es","fr"]'

#### Set Custom Download Location

    uv run python main.py config set paths.video_path "/path/to/videos"
    uv run python main.py config set paths.playlist_path "/path/to/playlists"

#### Apply Quality Preset

    uv run python main.py config preset quality

## 📁 Project Structure

    youtube-downloader/
    ├── src/
    │   └── ytdl/
    │       ├── __init__.py       # Package initialization
    │       ├── cli.py            # Command-line interface
    │       ├── config.py         # Configuration management
    │       ├── downloader.py     # Download logic
    │       └── utils.py          # Utility functions
    ├── .github/
    │   └── workflows/
    │       └── ci.yml            # GitHub Actions CI
    ├── main.py                   # Entry point
    ├── config.json               # Configuration file
    ├── youtube_links.txt         # URLs to download
    ├── pyproject.toml            # Project metadata
    ├── run.sh                    # Linux/macOS launcher
    ├── run.bat                   # Windows launcher
    ├── .gitignore                # Git ignore rules
    ├── .python-version           # Python version
    ├── LICENSE                   # MIT license
    ├── README.md                 # This file
    └── CONTRIBUTING.md           # Contribution guidelines

## 🎯 Use Cases

### Download a Course/Tutorial Playlist

1. Add playlist URL to `youtube_links.txt`
2. Apply archive preset:

       uv run python main.py config preset archive

3. Run the downloader

### Batch Download with Bandwidth Limit

    # Set 5MB/s limit
    uv run python main.py config set download.max_download_rate "5M"

    # Add URLs and download
    uv run python main.py

### Download Only Audio (Podcast/Music)

    uv run python main.py config set download.format "bestaudio[ext=m4a]"
    uv run python main.py config set download.merge_format "m4a"

### Download with Subtitles

    uv run python main.py config set metadata.embed_subtitles true
    uv run python main.py config set metadata.subtitle_languages '["en"]'
    uv run python main.py config set metadata.auto_subtitles true

## 🔧 Advanced Usage

### Using Cookies for Authentication

Some videos require authentication. Export cookies from your browser:

1. Install a browser extension like "Get cookies.txt LOCALLY"
2. Export cookies to `cookies.txt`
3. Configure:

       uv run python main.py config set advanced.cookies_file "cookies.txt"

### Using a Proxy

    uv run python main.py config set advanced.proxy "http://proxy.example.com:8080"

### Bypass Geo-restrictions

    uv run python main.py config set advanced.geo_bypass true

### Custom Format String

For advanced users, customize the download format:

    # Download 1080p video + best audio
    uv run python main.py config set download.format "bestvideo[height<=1080]+bestaudio"

    # Download only MP4 formats
    uv run python main.py config set download.format "bestvideo[ext=mp4]+bestaudio[ext=m4a]"

## 🐛 Troubleshooting

### "uv: command not found"

Install uv following the installation instructions above.

### "ffmpeg not found"

Install ffmpeg for your platform. See ffmpeg installation section above.

### "HTTP Error 429: Too Many Requests"

YouTube is rate-limiting you. Solutions:

1. Increase `request_delay`:

       uv run python main.py config set download.request_delay 10

2. Wait 30-60 minutes before trying again
3. Use a proxy or VPN

### Downloads Fail Silently

Check the log file:

    cat download.log  # Linux/macOS
    type download.log  # Windows

### "Insufficient disk space"

Free up space or change download location:

    uv run python main.py config set paths.video_path "/path/with/more/space"

### Videos Download but Don't Merge

Install ffmpeg properly and ensure it's in your PATH:

    ffmpeg -version

### Subtitles Not Downloading

1. Check if video has subtitles: `yt-dlp --list-subs VIDEO_URL`
2. Verify configuration:

       uv run python main.py config get metadata.embed_subtitles

3. Enable subtitles:

       uv run python main.py config set metadata.embed_subtitles true

### Colors Not Showing

Enable colors:

    uv run python main.py config set features.use_colors true

Or disable if terminal doesn't support ANSI:

    uv run python main.py config set features.use_colors false

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

    # Clone the repository
    git clone https://github.com/Neshant-SB/youtube-downloader.git
    cd youtube-downloader

    # Install development dependencies
    uv sync --all-extras

    # Run tests
    uv run pytest

    # Run linter
    uv run ruff check .

    # Format code
    uv run ruff format .

    # Type checking
    uv run mypy src/

### Running Tests

    # Run all tests
    uv run pytest

    # Run with coverage
    uv run pytest --cov=src/ytdl --cov-report=html

    # View coverage report
    open htmlcov/index.html

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The best YouTube downloader
- Uses [SponsorBlock](https://sponsor.ajay.app/) - Skip sponsored segments
- Package management by [uv](https://github.com/astral-sh/uv) - Blazingly fast Python package installer
- Video processing by [ffmpeg](https://ffmpeg.org/) - Complete multimedia solution

## 📊 Stats

- **Lines of Code:** ~2000
- **Languages:** Python 3.11+
- **Dependencies:** 2 runtime, 5 dev
- **Platforms:** Windows, macOS, Linux
- **License:** MIT

## 🗺️ Roadmap

- [ ] Add download queue management
- [ ] Implement download scheduling
- [ ] Add GUI interface
- [ ] Support for more platforms (Vimeo, Twitch, etc.)
- [ ] Download history and statistics
- [ ] Concurrent downloads
- [ ] Video format conversion
- [ ] Automatic updates check

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Neshant-SB/youtube-downloader/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Neshant-SB/youtube-downloader/discussions)
- **Email:** neshantsb@gmail.com

## ⭐ Star History

If you find this project useful, please consider giving it a star!

[![Star History Chart](https://api.star-history.com/svg?repos=Neshant-SB/youtube-downloader&type=Date)](https://star-history.com/#Neshant-SB/youtube-downloader&Date)

---

Made with ❤️ by [Neshant S B](https://github.com/Neshant-SB)