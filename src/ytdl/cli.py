"""Command-line interface for YouTube Downloader."""

from __future__ import annotations

import sys
from pathlib import Path

from ytdl.config import PRESETS, ConfigManager
from ytdl.downloader import DownloadManager
from ytdl.utils import colored


def print_version() -> None:
    """Print version information."""
    from ytdl import __version__

    print(f"YouTube Downloader v{__version__}")


def print_help() -> None:
    """Print help information."""
    print(colored("\nYouTube Downloader", "bold"))
    print(colored("=" * 60, "dim"))
    print("\nUsage:")
    print("  ytdl [command] [options]")
    print("\nCommands:")
    print(colored("  Download:", "bold"))
    print("    (no arguments)           - Start downloading")
    print("    download                 - Start downloading")
    print(colored("\n  Configuration:", "bold"))
    print("    config                   - Interactive config menu")
    print("    config view [section]    - View configuration")
    print("    config get <key>         - Get config value")
    print("    config set <key> <value> - Set config value")
    print("    config preset <name>     - Apply preset")
    print("    config reset             - Reset to defaults")
    print("    config validate          - Validate configuration")
    print(colored("\n  Info:", "bold"))
    print("    --version, -v            - Show version")
    print("    --help, -h               - Show this help")
    print("\nExamples:")
    print("  ytdl")
    print("  ytdl config")
    print("  ytdl config view download")
    print("  ytdl config set download.max_retries 5")
    print("  ytdl config preset quality")
    print()


def cmd_download(config_file: Path | None = None) -> int:
    """Run the downloader."""
    config_manager = ConfigManager(config_file)
    manager = DownloadManager(config_manager)

    try:
        success = manager.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        print()
        print(colored("\n[CANCELLED] Download interrupted", "yellow"))
        return 1


def cmd_config(args: list[str]) -> int:
    """Handle config commands."""
    config_manager = ConfigManager()

    if not args:
        config_manager.interactive_menu()
        return 0

    subcmd = args[0].lower()

    if subcmd == "view":
        section = args[1] if len(args) > 1 else None
        if section:
            config_manager.display_section(section)
        else:
            config_manager.display_all()
        return 0

    elif subcmd == "get":
        if len(args) < 2:
            print(colored("Error: Missing key", "red"))
            return 1

        value = config_manager.get_value(args[1])
        if value is None:
            print(colored(f"Setting '{args[1]}' not found", "red"))
            return 1

        print(config_manager.display_value(value))
        return 0

    elif subcmd == "set":
        if len(args) < 3:
            print(colored("Error: Missing key or value", "red"))
            return 1

        if config_manager.set_value(args[1], args[2]):
            print(colored(f"✓ Set {args[1]} = {args[2]}", "green"))
            return 0
        else:
            print(colored("✗ Failed to update setting", "red"))
            return 1

    elif subcmd == "preset":
        if len(args) < 2:
            config_manager.display_presets()
            return 0

        preset_name = args[1]
        if preset_name not in PRESETS:
            print(colored(f"Preset '{preset_name}' not found", "red"))
            config_manager.display_presets()
            return 1

        if config_manager.apply_preset(preset_name):
            print(colored(f"✓ Applied preset: {preset_name}", "green"))
            return 0
        else:
            print(colored("✗ Failed to apply preset", "red"))
            return 1

    elif subcmd == "reset":
        if config_manager.reset():
            print(colored("✓ Configuration reset to defaults", "green"))
            return 0
        else:
            print(colored("✗ Failed to reset configuration", "red"))
            return 1

    elif subcmd == "validate":
        issues = config_manager.validate()
        if issues:
            print(colored("⚠ Issues found:", "yellow"))
            for issue in issues:
                print(colored(f"  • {issue}", "red"))
            return 1
        else:
            print(colored("✓ Configuration is valid", "green"))
            return 0

    elif subcmd == "backup":
        backup_path = config_manager.backup()
        if backup_path:
            print(colored(f"✓ Backup created: {backup_path}", "green"))
            return 0
        else:
            print(colored("✗ Failed to create backup", "red"))
            return 1

    else:
        print(colored(f"Unknown config command: {subcmd}", "red"))
        return 1


def main() -> int:
    """Main entry point for CLI."""
    args = sys.argv[1:]

    if not args:
        return cmd_download()

    cmd = args[0].lower()

    if cmd in ("--help", "-h", "help"):
        print_help()
        return 0

    if cmd in ("--version", "-v", "version"):
        print_version()
        return 0

    if cmd == "download":
        return cmd_download()

    if cmd == "config":
        return cmd_config(args[1:])

    print(colored(f"Unknown command: {cmd}", "red"))
    print_help()
    return 1


def wait_for_exit() -> None:
    """Wait for user input before exiting."""
    print()
    input("Press Enter to exit...")


def main_with_wait() -> int:
    """Main entry point that waits for exit."""
    try:
        return main()
    except KeyboardInterrupt:
        print(colored("\n\n[CANCELLED]", "yellow"))
        return 1
    except Exception as e:
        print(colored(f"\n[ERROR] {e}", "red"))
        import traceback

        traceback.print_exc()
        return 1
    finally:
        wait_for_exit()


if __name__ == "__main__":
    sys.exit(main())
