"""Command executor for slash commands.

Handles command detection, expansion, and sequential execution
to prevent race conditions from rapid command submissions.
"""

import asyncio
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from .loader import SlashCommandLoader, UnknownCommandError

logger = structlog.get_logger(__name__)

# Pattern to match slash commands
# Matches: /word.word, /word-word, /word_word patterns
# Does NOT match: /help, /start, /status (single word commands - these are bot commands)
SLASH_COMMAND_PATTERN = re.compile(r"^/([a-zA-Z0-9]+[.\-_][a-zA-Z0-9.\-_]+)\s*(.*)?$")


def is_slash_command(message: str) -> bool:
    """Check if a message is a slash command.

    Slash commands have the format /name.subname or /name-subname.
    Single-word commands like /help are NOT slash commands (they're bot commands).

    Args:
        message: Message text to check

    Returns:
        True if message is a slash command
    """
    return bool(SLASH_COMMAND_PATTERN.match(message.strip()))


def parse_slash_command(message: str) -> Optional[Dict[str, str]]:
    """Parse a slash command message.

    Args:
        message: Message text

    Returns:
        Dict with 'command' and 'arguments' or None if not a command
    """
    match = SLASH_COMMAND_PATTERN.match(message.strip())
    if not match:
        return None

    command = match.group(1)
    arguments = match.group(2) or ""

    return {
        "command": command,
        "arguments": arguments.strip(),
    }


class CommandExecutor:
    """Execute slash commands with sequential queue.

    Provides:
    - Command detection and parsing
    - Template loading and expansion
    - Sequential execution queue to prevent race conditions
    - Error handling with available command hints
    """

    def __init__(
        self,
        commands_dir: Optional[Path] = None,
        enable_queue: bool = True,
    ) -> None:
        """Initialize the command executor.

        Args:
            commands_dir: Path to commands directory
            enable_queue: Enable sequential execution queue
        """
        self.loader = SlashCommandLoader(commands_dir)
        self.enable_queue = enable_queue
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._processing: Dict[int, bool] = {}  # user_id -> is_processing
        self._lock = asyncio.Lock()

    async def process_message(
        self,
        message: str,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process a message, detecting and expanding slash commands.

        Args:
            message: Message text
            user_id: Optional user ID for queue management

        Returns:
            Result dict with:
            - is_command: bool
            - original_message: str
            - expanded_prompt: str (if command)
            - command: str (if command)
            - arguments: str (if command)
            - error: str (if error)
        """
        result: Dict[str, Any] = {
            "is_command": False,
            "original_message": message,
            "expanded_prompt": None,
            "command": None,
            "arguments": None,
            "error": None,
        }

        # Check if it's a slash command
        parsed = parse_slash_command(message)
        if not parsed:
            return result

        result["is_command"] = True
        result["command"] = parsed["command"]
        result["arguments"] = parsed["arguments"]

        # Check if user has command in progress
        if self.enable_queue and user_id is not None:
            async with self._lock:
                if self._processing.get(user_id, False):
                    result["error"] = (
                        "A command is already in progress. "
                        "Please wait for it to complete."
                    )
                    return result
                self._processing[user_id] = True

        try:
            # Expand the command
            expanded = self.loader.expand(
                parsed["command"],
                parsed["arguments"],
            )
            result["expanded_prompt"] = expanded

            logger.info(
                "Expanded slash command",
                command=parsed["command"],
                arguments_length=len(parsed["arguments"]),
            )

        except UnknownCommandError as e:
            result["error"] = self._format_unknown_command_error(e)
            logger.warning(
                "Unknown slash command",
                command=parsed["command"],
                available=e.available_commands,
            )

        except Exception as e:
            result["error"] = f"Failed to process command: {str(e)}"
            logger.error(
                "Command processing failed",
                command=parsed["command"],
                error=str(e),
            )

        finally:
            # Clear processing flag
            if self.enable_queue and user_id is not None:
                async with self._lock:
                    self._processing[user_id] = False

        return result

    def _format_unknown_command_error(self, error: UnknownCommandError) -> str:
        """Format an unknown command error with helpful hints.

        Args:
            error: UnknownCommandError instance

        Returns:
            Formatted error message
        """
        lines = [
            f"Unknown command: `/{error.command}`",
            "",
            "**Available commands:**",
        ]

        if error.available_commands:
            for cmd in sorted(error.available_commands):
                lines.append(f"  • `/{cmd}`")
        else:
            lines.append("  (no commands discovered)")

        lines.extend(
            [
                "",
                "Commands are loaded from `.claude/commands/*.md`",
            ]
        )

        return "\n".join(lines)

    def list_commands(self) -> List[str]:
        """List all available commands.

        Returns:
            List of command names
        """
        return self.loader.list_commands()

    def has_command(self, command: str) -> bool:
        """Check if a command exists.

        Args:
            command: Command name

        Returns:
            True if command exists
        """
        return self.loader.has_command(command)

    def reload_commands(self) -> None:
        """Reload commands from directory."""
        self.loader.reload()

    async def mark_complete(self, user_id: int) -> None:
        """Mark a user's command as complete.

        Args:
            user_id: User ID
        """
        async with self._lock:
            self._processing[user_id] = False

    def is_user_processing(self, user_id: int) -> bool:
        """Check if user has a command in progress.

        Args:
            user_id: User ID

        Returns:
            True if user has command in progress
        """
        return self._processing.get(user_id, False)


# Module-level convenience functions
_default_executor: Optional[CommandExecutor] = None


def get_executor(commands_dir: Optional[Path] = None) -> CommandExecutor:
    """Get or create the default command executor.

    Args:
        commands_dir: Optional commands directory path

    Returns:
        CommandExecutor instance
    """
    global _default_executor
    if _default_executor is None:
        _default_executor = CommandExecutor(commands_dir)
    return _default_executor


def set_executor(executor: CommandExecutor) -> None:
    """Set the default command executor.

    Args:
        executor: CommandExecutor instance to use as default
    """
    global _default_executor
    _default_executor = executor
