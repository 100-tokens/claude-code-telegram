"""Slash command expansion for Claude Code workflows.

This module discovers and expands slash commands from .claude/commands/
directory, enabling Claude Code workflows from Telegram.
"""

from .executor import (
    CommandExecutor,
    get_executor,
    is_slash_command,
    parse_slash_command,
    set_executor,
)
from .loader import (
    SlashCommandLoader,
    UnknownCommandError,
)

__all__ = [
    # Loader
    "SlashCommandLoader",
    "UnknownCommandError",
    # Executor
    "CommandExecutor",
    "get_executor",
    "set_executor",
    "is_slash_command",
    "parse_slash_command",
]
