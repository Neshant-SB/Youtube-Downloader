#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "YouTube Downloader"
echo "========================================"
echo

if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo
    echo "Install uv:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  brew install uv"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg is not installed"
    echo "Install: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
    echo
    read -p "Press Enter to continue or Ctrl+C to cancel..."
fi

echo "Syncing dependencies..."
uv sync
echo

echo "Starting downloader..."
echo
uv run python main.py