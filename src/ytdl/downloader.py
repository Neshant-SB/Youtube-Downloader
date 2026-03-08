"""Main downloader logic for YouTube Downloader."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from ytdl.config import Config, ConfigManager
from ytdl.utils import (
    IS_WINDOWS,
    check_disk_space,
    clear_line,
    colored,
    format_bytes,
    format_duration,
    is_playlist_url,
    log,
    parse_error_message,
    print_progress,
    run_command,
    sanitize_filename,
    set_color_enabled,
)


def get_video_info(url: str, config: Config) -> dict[str, Any] | None:
    """Get video information from YouTube."""
    cmd = ["yt-dlp", "--dump-json", "--no-warnings", "--no-playlist", url]

    if config.user_agent:
        cmd.extend(["--user-agent", config.user_agent])
    if config.proxy:
        cmd.extend(["--proxy", config.proxy])
    if config.geo_bypass:
        cmd.append("--geo-bypass")
    if config.cookies_file:
        cmd.extend(["--cookies", config.cookies_file])

    success, stdout, _ = run_command(cmd, timeout=60)

    if success and stdout:
        try:
            data = json.loads(stdout.strip().split("\n")[0])
            return data  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            pass
    return None


def get_playlist_info(url: str, config: Config) -> tuple[str, list[dict[str, Any]]]:
    """Get playlist title and video entries."""
    cmd_title = [
        "yt-dlp",
        "--no-download",
        "--no-warnings",
        "--flat-playlist",
        "--print",
        "%(playlist_title)s",
        "--playlist-items",
        "1",
        url,
    ]

    success, stdout, _ = run_command(cmd_title, timeout=60)

    playlist_title = None
    if success and stdout.strip() and stdout.strip().lower() not in ("na", "none", ""):
        playlist_title = stdout.strip().split("\n")[0]

    cmd_entries = ["yt-dlp", "--dump-json", "--flat-playlist", "--no-warnings", url]
    success, stdout, _ = run_command(cmd_entries, timeout=180)

    entries: list[dict[str, Any]] = []
    if success:
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                if not playlist_title:
                    if data.get("_type") == "playlist":
                        playlist_title = data.get("title")
                    elif data.get("playlist_title"):
                        playlist_title = data.get("playlist_title")
                    elif data.get("playlist"):
                        playlist_title = data.get("playlist")

                if "id" in data and data.get("_type") != "playlist":
                    entries.append(data)
            except json.JSONDecodeError:
                continue

    if not playlist_title:
        if "list=" in url:
            playlist_id = url.split("list=")[1].split("&")[0]
            playlist_title = f"Playlist_{playlist_id[:12]}"
        else:
            playlist_title = f"Playlist_{int(time.time())}"

    valid_entries: list[dict[str, Any]] = []
    for entry in entries:
        if not entry.get("id"):
            continue

        availability = entry.get("availability", "")
        if availability in ("private", "premium_only", "subscriber_only", "needs_auth"):
            continue

        title = entry.get("title", "").lower()
        if title in ("[private video]", "[deleted video]", "private video", "deleted video"):
            continue

        valid_entries.append(entry)

    return sanitize_filename(playlist_title, config.max_filename_length), valid_entries


def check_sponsorblock() -> bool:
    """Check if SponsorBlock is available."""
    try:
        cmd = [
            "yt-dlp",
            "--simulate",
            "--sponsorblock-mark",
            "all",
            "--no-warnings",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ]
        success, _, stderr = run_command(cmd, timeout=10)
        return "sponsorblock" not in stderr.lower() or success
    except Exception:
        return False


def check_file_exists(output_dir: Path, filename: str, extensions: list[str]) -> Path | None:
    """Check if a file already exists with any video extension."""
    if not output_dir.exists():
        return None

    for ext in extensions:
        file_path = output_dir / f"{filename}{ext}"
        if file_path.exists():
            return file_path

    try:
        clean_filename = re.sub(r"[^\w\s-]", "", filename.lower()).strip()

        for existing_file in output_dir.iterdir():
            if existing_file.is_file() and existing_file.suffix.lower() in extensions:
                clean_existing = re.sub(r"[^\w\s-]", "", existing_file.stem.lower()).strip()

                if clean_filename == clean_existing:
                    return existing_file

                if len(clean_filename) > 20 and clean_filename in clean_existing:
                    return existing_file

                if len(clean_filename) > 20 and len(clean_existing) > 20:
                    if clean_filename[:50] == clean_existing[:50]:
                        return existing_file
    except Exception:
        pass

    return None


class DownloadManager:
    """Main download manager class."""

    def __init__(self, config_manager: ConfigManager | None = None) -> None:
        """Initialize DownloadManager."""
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.config

        self.videos: list[tuple[str, str]] = []
        self.playlists: list[tuple[str, str, list[dict[str, Any]]]] = []

        self.downloaded = 0
        self.skipped = 0
        self.failed = 0
        self.start_time = time.time()

        self._sponsorblock_ok: bool | None = None

        set_color_enabled(self.config.use_colors)

        self.config.temp_path.mkdir(parents=True, exist_ok=True)
        self.config.links_file.parent.mkdir(parents=True, exist_ok=True)

        log(self.config.log_file, "INFO", "=" * 60)
        log(self.config.log_file, "INFO", "Session started")

    def _create_temp_dir(self) -> Path:
        """Create a unique temporary directory."""
        for _ in range(10):
            temp_dir = self.config.temp_path / f"dl_{uuid.uuid4().hex[:12]}"
            try:
                temp_dir.mkdir(parents=True, exist_ok=False)
                return temp_dir
            except FileExistsError:
                continue

        temp_dir = self.config.temp_path / f"dl_{int(time.time() * 1000000)}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    def read_links(self) -> bool:
        """Read URLs from the links file."""
        if not self.config.links_file.exists():
            self.config.links_file.touch()
            print(f"Created: {self.config.links_file}")
            print()
            print("Add YouTube URLs (one per line) and run again.")
            return False

        try:
            with open(self.config.links_file, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(colored(f"Error reading file: {e}", "red"))
            return False

        video_urls: list[str] = []
        playlist_urls: list[str] = []

        for line in lines:
            url = line.strip()
            if url and not url.startswith("#"):
                if is_playlist_url(url):
                    playlist_urls.append(url)
                else:
                    video_urls.append(url)

        if not video_urls and not playlist_urls:
            print("No links found.")
            print()
            print(f"Add URLs to: {self.config.links_file}")
            return False

        print(
            f"Found: {colored(str(len(video_urls)), 'cyan')} video(s), "
            f"{colored(str(len(playlist_urls)), 'cyan')} playlist(s)"
        )
        print()
        log(
            self.config.log_file,
            "INFO",
            f"Found {len(video_urls)} videos, {len(playlist_urls)} playlists",
        )

        has_space, free_gb = check_disk_space(self.config.video_path)
        if free_gb != -1:
            if not has_space:
                print(colored(f"⚠ Warning: Low disk space ({free_gb:.2f} GB free)", "red"))
                print()
            elif free_gb < self.config.min_disk_space_gb * 5:
                print(colored(f"ℹ Disk space: {free_gb:.2f} GB free", "yellow"))
                print()

        if video_urls:
            print("Loading video info...")
            for i, url in enumerate(video_urls, 1):
                print_progress(f"  Video {i}/{len(video_urls)}...")
                info = get_video_info(url, self.config)
                title = sanitize_filename(
                    info.get("title", "Unknown") if info else "Unknown",
                    self.config.max_filename_length,
                )
                self.videos.append((url, title))
            clear_line()
            print(f"  Loaded {colored(str(len(self.videos)), 'green')} video(s)")

        if playlist_urls:
            print("Loading playlist info...")
            for i, url in enumerate(playlist_urls, 1):
                print_progress(f"  Playlist {i}/{len(playlist_urls)}...")
                title, entries = get_playlist_info(url, self.config)
                clear_line()
                if entries:
                    self.playlists.append((url, title, entries))
                    print(
                        f"  [{i}] {colored(title, 'cyan')} "
                        f"({colored(str(len(entries)), 'green')} videos)"
                    )
                    log(
                        self.config.log_file,
                        "INFO",
                        f"Playlist: {title} ({len(entries)} videos)",
                        url,
                    )
                else:
                    print(colored(f"  [{i}] Failed to load playlist", "red"))
            print()

        return True

    def _remove_link(self, url: str) -> None:
        """Remove a URL from the links file."""
        if not self.config.remove_completed_links:
            return

        try:
            with open(self.config.links_file, encoding="utf-8") as f:
                lines = f.readlines()

            with open(self.config.links_file, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.strip() != url:
                        f.write(line)
        except Exception:
            pass

    def _download_video(
        self,
        url: str,
        output_dir: Path,
        video_num: int | None = None,
        skip_existing: bool = True,
    ) -> tuple[bool, bool]:
        """Download a single video. Returns (success, was_skipped)."""
        info = get_video_info(url, self.config)
        if not info:
            print(colored("  ✗ Failed to get video info", "red"))
            log(self.config.log_file, "ERROR", "Failed to get video info", url)
            return False, False

        title = sanitize_filename(
            info.get("title", "Unknown"),
            self.config.max_filename_length,
        )
        duration = info.get("duration", 0) or 0
        has_chapters = bool(info.get("chapters"))

        if video_num is not None:
            output_name = f"({video_num:02d}) {title}"
        else:
            output_name = title

        if skip_existing and self.config.skip_existing:
            existing = check_file_exists(output_dir, output_name, self.config.video_extensions)
            if existing:
                print(f"  Title:    {title}")
                print(f"  Duration: {format_duration(duration)}")
                print(colored("  ⏭ Skipped: Already exists", "yellow"))
                print(f"  File: {existing.name}")
                log(self.config.log_file, "SKIPPED", f"{output_name} | Already exists", url)
                return True, True

        print(f"  Title:    {title}")
        print(f"  Duration: {format_duration(duration)}")

        has_space, free_gb = check_disk_space(output_dir, self.config.min_disk_space_gb)
        if not has_space:
            print(
                colored(
                    f"  ✗ Insufficient disk space ({free_gb:.2f} GB free, "
                    f"need {self.config.min_disk_space_gb} GB)",
                    "red",
                )
            )
            log(self.config.log_file, "ERROR", f"Insufficient disk space: {free_gb:.2f} GB", url)
            return False, False
        elif free_gb != -1 and free_gb < self.config.min_disk_space_gb * 2:
            print(colored(f"  ⚠ Warning: Low disk space ({free_gb:.2f} GB free)", "yellow"))

        temp_dir = self._create_temp_dir()
        output_template = str(temp_dir / "%(title)s.%(ext)s")

        cmd = [
            "yt-dlp",
            "-f",
            self.config.format,
            "--merge-output-format",
            self.config.merge_format,
            "--newline",
            "--progress",
            "--no-warnings",
            "-o",
            output_template,
        ]

        if self.config.continue_partial:
            cmd.extend(["--continue", "--no-part"])

        if self.config.max_download_rate:
            cmd.extend(["--limit-rate", self.config.max_download_rate])

        if self.config.max_resolution:
            cmd.extend(
                [
                    "-f",
                    f"bestvideo[height<={self.config.max_resolution}]+bestaudio/"
                    f"best[height<={self.config.max_resolution}]",
                ]
            )

        if self.config.max_filesize:
            cmd.extend(["--max-filesize", self.config.max_filesize])

        if self.config.prefer_free_formats:
            cmd.append("--prefer-free-formats")

        if self.config.embed_thumbnail:
            cmd.append("--embed-thumbnail")

        if self.config.embed_metadata:
            cmd.append("--embed-metadata")

        if self.config.embed_subtitles:
            cmd.append("--embed-subs")
            cmd.extend(["--sub-langs", ",".join(self.config.subtitle_languages)])
            if self.config.auto_subtitles:
                cmd.append("--write-auto-subs")

        if has_chapters and self.config.embed_chapters:
            cmd.append("--embed-chapters")

        if self._sponsorblock_ok is None:
            self._sponsorblock_ok = self.config.sponsorblock_enabled and check_sponsorblock()

        if self._sponsorblock_ok:
            cmd.extend(
                [
                    "--sponsorblock-mark",
                    ",".join(self.config.sponsorblock_categories),
                ]
            )

        if self.config.user_agent:
            cmd.extend(["--user-agent", self.config.user_agent])
        if self.config.proxy:
            cmd.extend(["--proxy", self.config.proxy])
        if self.config.geo_bypass:
            cmd.append("--geo-bypass")
        if self.config.age_limit:
            cmd.extend(["--age-limit", str(self.config.age_limit)])
        if self.config.cookies_file:
            cmd.extend(["--cookies", self.config.cookies_file])

        cmd.append(url)

        start_time = time.time()
        success = False

        try:
            kwargs: dict[str, Any] = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "bufsize": 1,
            }

            if IS_WINDOWS:
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(cmd, **kwargs)

            if process.stdout is None:
                raise RuntimeError("Failed to capture yt-dlp output")

            progress_re = re.compile(
                r"\[download\]\s+([\d.]+)%\s+of\s+~?([\d.]+)(\w+)"
                r"(?:\s+at\s+([\d.]+)(\w+)/s)?"
                r"(?:\s+ETA\s+(\S+))?"
            )

            last_pct = -1
            output_lines: list[str] = []

            for line in process.stdout:
                line = line.strip()
                output_lines.append(line)

                match = progress_re.search(line)
                if match:
                    pct = float(match.group(1))
                    if int(pct) != last_pct:
                        last_pct = int(pct)
                        download_size = f"{match.group(2)}{match.group(3)}"
                        speed = f"{match.group(4)}{match.group(5)}/s" if match.group(4) else "---"
                        eta = match.group(6) if match.group(6) else "--:--"

                        if pct < 33:
                            pct_color = "red"
                        elif pct < 66:
                            pct_color = "yellow"
                        else:
                            pct_color = "green"

                        pct_str = colored(f"{pct:5.1f}%", pct_color)
                        print_progress(
                            f"  Progress: {pct_str} | {download_size:>10} | {speed:>12} | ETA: {eta}"
                        )
                elif "[Merger]" in line:
                    print_progress(colored("  Merging video and audio...", "cyan"))
                elif "[SponsorBlock]" in line:
                    print_progress(colored("  Adding SponsorBlock markers...", "cyan"))
                elif "[EmbedThumbnail]" in line:
                    print_progress(colored("  Embedding thumbnail...", "cyan"))

            process.wait()
            clear_line()

            output_files: list[Path] = []
            for ext in self.config.video_extensions:
                output_files.extend(list(temp_dir.glob(f"*{ext}")))

            if not output_files:
                output_files = list(temp_dir.glob("*.*"))

            if output_files:
                source = output_files[0]
                output_dir.mkdir(parents=True, exist_ok=True)

                final = output_dir / f"{output_name}{source.suffix}"
                n = 1
                while final.exists():
                    final = output_dir / f"{output_name} ({n}){source.suffix}"
                    n += 1

                shutil.move(str(source), str(final))

                file_size = final.stat().st_size
                elapsed = time.time() - start_time

                print(
                    colored(
                        f"  ✓ Done: {format_bytes(file_size)} in {format_duration(int(elapsed))}",
                        "green",
                    )
                )
                print(f"  Saved: {final.name}")
                log(
                    self.config.log_file,
                    "SUCCESS",
                    f"{output_name} | {format_bytes(file_size)} | {format_duration(int(elapsed))}",
                    url,
                )
                success = True
            else:
                errors = [line for line in output_lines if "ERROR" in line]
                raw_msg = errors[-1] if errors else "No output file"
                msg = parse_error_message(raw_msg)
                print(colored(f"  ✗ Failed: {msg}", "red"))
                log(self.config.log_file, "ERROR", f"{output_name} | {msg}", url)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            error_msg = parse_error_message(str(e))
            print(colored(f"  ✗ Error: {error_msg}", "red"))
            log(self.config.log_file, "ERROR", f"{title} | {error_msg}", url)

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return success, False

    def _download_with_retry(
        self,
        url: str,
        output_dir: Path,
        video_num: int | None = None,
    ) -> tuple[bool, bool]:
        """Download with retry logic."""
        success, skipped = self._download_video(url, output_dir, video_num, skip_existing=True)

        if success or skipped:
            return success, skipped

        for attempt in range(1, self.config.max_retries):
            print(colored(f"  Retry {attempt + 1}/{self.config.max_retries}...", "yellow"))
            time.sleep(self.config.retry_delay * (attempt + 1))

            success, _ = self._download_video(url, output_dir, video_num, skip_existing=False)
            if success:
                return True, False

        log(
            self.config.log_file,
            "FAILED",
            f"Failed after {self.config.max_retries} retries",
            url,
        )
        return False, False

    def download_videos(self) -> None:
        """Download all individual videos."""
        if not self.videos:
            return

        self.config.video_path.mkdir(parents=True, exist_ok=True)

        print()
        print(colored("=" * 60, "bold"))
        print(colored(f"DOWNLOADING VIDEOS ({len(self.videos)})", "bold"))
        print(colored("=" * 60, "bold"))

        for i, (url, title) in enumerate(self.videos, 1):
            print()
            print(colored(f"[{i}/{len(self.videos)}] {title}", "cyan"))
            print("-" * 50)

            success, skipped = self._download_with_retry(url, self.config.video_path)

            if skipped:
                self.skipped += 1
                self._remove_link(url)
            elif success:
                self.downloaded += 1
                self._remove_link(url)
            else:
                self.failed += 1

            if i < len(self.videos):
                time.sleep(self.config.request_delay)

    def download_playlists(self) -> None:
        """Download all playlists."""
        if not self.playlists:
            return

        print()
        print(colored("=" * 60, "bold"))
        print(colored(f"DOWNLOADING PLAYLISTS ({len(self.playlists)})", "bold"))
        print(colored("=" * 60, "bold"))

        for i, (url, title, entries) in enumerate(self.playlists, 1):
            print()
            print(colored(f"[{i}/{len(self.playlists)}] {title}", "magenta"))
            print(f"  Videos: {colored(str(len(entries)), 'cyan')}")

            if not entries:
                print(colored("  Playlist is empty, skipping", "yellow"))
                continue

            if i == 1:
                self.config.playlist_path.mkdir(parents=True, exist_ok=True)

            playlist_dir = self.config.playlist_path / title
            playlist_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Folder: {playlist_dir}")
            print(colored("=" * 60, "bold"))

            all_ok = True
            playlist_downloaded = 0
            playlist_skipped = 0

            for j, entry in enumerate(entries, 1):
                video_id = entry.get("id", "")
                if not video_id:
                    print(colored(f"  [{j}/{len(entries)}] Skipped - no video ID", "yellow"))
                    continue

                print()
                print(colored(f"  [{j}/{len(entries)}]", "blue"))

                video_url = f"https://www.youtube.com/watch?v={video_id}"
                success, skipped = self._download_with_retry(video_url, playlist_dir, video_num=j)

                if skipped:
                    self.skipped += 1
                    playlist_skipped += 1
                elif success:
                    self.downloaded += 1
                    playlist_downloaded += 1
                else:
                    self.failed += 1
                    all_ok = False

                if j < len(entries):
                    time.sleep(self.config.request_delay)

            print()
            print(
                f"  Downloaded: {colored(str(playlist_downloaded), 'green')}, "
                f"Skipped: {colored(str(playlist_skipped), 'yellow')}, "
                f"Total: {len(entries)}"
            )

            if all_ok:
                self._remove_link(url)
                print(colored(f"  ✓ Playlist complete: {title}", "green"))
                log(
                    self.config.log_file,
                    "SUCCESS",
                    f"Playlist complete: {title} ({playlist_downloaded} new, "
                    f"{playlist_skipped} skipped)",
                    url,
                )
            else:
                print(colored(f"  ⚠ Playlist incomplete: {title}", "yellow"))
                log(self.config.log_file, "WARNING", f"Playlist incomplete: {title}", url)

    def print_summary(self) -> None:
        """Print download summary."""
        elapsed = time.time() - self.start_time

        print()
        print(colored("=" * 60, "bold"))
        print(colored("DOWNLOAD COMPLETE", "bold"))
        print(colored("=" * 60, "bold"))
        print(f"  Downloaded: {colored(str(self.downloaded), 'green')}")
        print(f"  Skipped:    {colored(str(self.skipped), 'yellow')}")
        print(f"  Failed:     {colored(str(self.failed), 'red') if self.failed > 0 else '0'}")
        print(f"  Time:       {format_duration(int(elapsed))}")
        print(colored("=" * 60, "bold"))

        log(
            self.config.log_file,
            "INFO",
            f"Session complete: {self.downloaded} downloaded, {self.skipped} skipped, "
            f"{self.failed} failed, {format_duration(int(elapsed))}",
        )
        log(self.config.log_file, "INFO", "=" * 60)

    def run(self) -> bool:
        """Run the download manager."""
        print()
        print(colored("=" * 60, "bold"))
        print(colored("YOUTUBE DOWNLOADER", "bold"))
        print(colored("=" * 60, "bold"))
        print()

        if not self.read_links():
            return True

        self.download_videos()
        self.download_playlists()

        shutil.rmtree(self.config.temp_path, ignore_errors=True)

        self.print_summary()
        return self.failed == 0
