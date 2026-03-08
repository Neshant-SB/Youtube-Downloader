@echo off
setlocal enabledelayedexpansion

echo ========================================
echo YouTube Downloader
echo ========================================
echo.

cd /d "%~dp0"

uv --version >nul 2>&1
if errorlevel 1 (
    echo Error: uv is not installed
    echo.
    echo Install: irm https://astral.sh/uv/install.ps1 ^| iex
    pause
    exit /b 1
)

ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo Warning: ffmpeg is not installed
    echo Install: scoop install ffmpeg
    echo.
    pause
)

echo Syncing dependencies...
uv sync
if errorlevel 1 (
    echo Failed to sync dependencies.
    pause
    exit /b 1
)
echo.

echo Starting downloader...
echo.
uv run python main.py

if errorlevel 1 (
    echo.
    echo An error occurred.
    pause
)