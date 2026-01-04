"""CLI module for Claude Code Telegram Bot.

This module provides the command-line interface for starting and managing
the Telegram bot. It uses Click for CLI argument parsing and provides
user-friendly startup/shutdown messaging.
"""

from src.cli.commands import cli
from src.cli.display import display_banner, display_error, display_shutdown

__all__ = ["cli", "display_banner", "display_error", "display_shutdown"]
