#!/usr/bin/env python3
"""YouTube Downloader - Entry Point."""

import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from ytdl.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
