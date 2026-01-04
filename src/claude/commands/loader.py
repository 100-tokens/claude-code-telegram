"""Slash command loader for Claude Code workflows.

Discovers and loads command templates from .claude/commands/ directory,
enabling Claude Code workflows (speckit, ralph-wiggum) from Telegram.
"""

from pathlib import Path
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class UnknownCommandError(Exception):
    """Raised when an unknown slash command is requested."""

    def __init__(self, command: str, available_commands: List[str]) -> None:
        """Initialize with command name and available commands.

        Args:
            command: The unknown command name
            available_commands: List of available command names
        """
        self.command = command
        self.available_commands = available_commands
        super().__init__(
            f"Unknown command: {command}. "
            f"Available commands: {', '.join(available_commands) or 'none'}"
        )


class SlashCommandLoader:
    """Load and expand slash command templates.

    Discovers markdown templates from a commands directory and
    provides template expansion with argument substitution.
    """

    def __init__(
        self,
        commands_dir: Optional[Path] = None,
        default_dir: str = ".claude/commands",
    ) -> None:
        """Initialize the command loader.

        Args:
            commands_dir: Path to commands directory (optional)
            default_dir: Default relative path if commands_dir not specified
        """
        if commands_dir is None:
            commands_dir = Path(default_dir)

        self.commands_dir = Path(commands_dir)
        self.commands: Dict[str, str] = {}
        self._discover()

    def _discover(self) -> None:
        """Discover command templates in the commands directory."""
        if not self.commands_dir.exists():
            logger.warning(
                "Commands directory not found",
                path=str(self.commands_dir),
            )
            return

        if not self.commands_dir.is_dir():
            logger.warning(
                "Commands path is not a directory",
                path=str(self.commands_dir),
            )
            return

        # Find all .md files in the directory
        for md_file in self.commands_dir.glob("*.md"):
            command_name = (
                md_file.stem
            )  # e.g., "speckit.specify" from "speckit.specify.md"
            try:
                template_content = md_file.read_text(encoding="utf-8")
                self.commands[command_name] = template_content
                logger.debug(
                    "Discovered command",
                    name=command_name,
                    file=str(md_file),
                )
            except Exception as e:
                logger.error(
                    "Failed to load command template",
                    file=str(md_file),
                    error=str(e),
                )

        logger.info(
            "Command discovery complete",
            count=len(self.commands),
            commands=list(self.commands.keys()),
        )

    def expand(self, command: str, arguments: str) -> str:
        """Expand a command template with arguments.

        Args:
            command: Command name (without leading /)
            arguments: Arguments to substitute for $ARGUMENTS

        Returns:
            Expanded template content

        Raises:
            UnknownCommandError: If command is not found
        """
        template = self.commands.get(command)

        if template is None:
            raise UnknownCommandError(
                command=command,
                available_commands=self.list_commands(),
            )

        # Replace all occurrences of $ARGUMENTS
        expanded = template.replace("$ARGUMENTS", arguments)

        logger.debug(
            "Expanded command",
            command=command,
            arguments_length=len(arguments),
            expanded_length=len(expanded),
        )

        return expanded

    def list_commands(self) -> List[str]:
        """List all available command names.

        Returns:
            List of command names (without leading /)
        """
        return list(self.commands.keys())

    def has_command(self, command: str) -> bool:
        """Check if a command exists.

        Args:
            command: Command name to check

        Returns:
            True if command exists
        """
        return command in self.commands

    def get_template(self, command: str) -> Optional[str]:
        """Get the raw template for a command.

        Args:
            command: Command name

        Returns:
            Template content or None if not found
        """
        return self.commands.get(command)

    def reload(self) -> None:
        """Reload commands from directory.

        Useful if templates have been modified.
        """
        self.commands.clear()
        self._discover()
        logger.info("Commands reloaded", count=len(self.commands))
