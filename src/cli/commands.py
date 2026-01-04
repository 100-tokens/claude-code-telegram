"""CLI commands for Claude Code Telegram Bot.

This module provides the Click-based command-line interface for
starting and managing the Telegram bot.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import click

from src import __version__
from src.cli.display import display_banner, display_error, display_shutdown


def validate_directory(directory: Path) -> tuple[bool, str]:
    """Validate that a directory exists and is accessible.

    Args:
        directory: Path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not directory.exists():
        return False, f"Directory does not exist: {directory}"

    if not directory.is_dir():
        return False, f"Path is not a directory: {directory}"

    # Check read permissions
    try:
        list(directory.iterdir())
    except PermissionError:
        return False, f"Cannot access directory (permission denied): {directory}"

    return True, ""


def validate_config(directory: Path) -> tuple[bool, str, list[str]]:
    """Validate configuration in the specified directory.

    Args:
        directory: Directory to check for configuration

    Returns:
        Tuple of (is_valid, error_message, fix_steps)
    """
    env_file = directory / ".env"

    if not env_file.exists():
        return (
            False,
            "No .env file found in the current directory",
            [
                "Create a .env file in the current directory",
                "Add: TELEGRAM_BOT_TOKEN=your_token_here",
                "Add: TELEGRAM_BOT_USERNAME=your_bot_username",
            ],
        )

    # Read .env file to check for required fields
    try:
        env_content = env_file.read_text()
    except PermissionError:
        return (
            False,
            "Cannot read .env file (permission denied)",
            ["Check file permissions: chmod 644 .env"],
        )

    # Check for required fields
    if "TELEGRAM_BOT_TOKEN" not in env_content or not any(
        line.strip().startswith("TELEGRAM_BOT_TOKEN=")
        and len(line.split("=", 1)) > 1
        and line.split("=", 1)[1].strip()
        for line in env_content.splitlines()
    ):
        return (
            False,
            "TELEGRAM_BOT_TOKEN is not set",
            [
                "Add to your .env file: TELEGRAM_BOT_TOKEN=your_token_here",
                "Get a token from @BotFather on Telegram",
            ],
        )

    return True, "", []


@click.group(invoke_without_command=True)
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=False, path_type=Path),
    default=None,
    help="Working directory for the bot (defaults to current directory)",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Enable debug logging",
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to configuration file (legacy support)",
)
@click.version_option(version=__version__, prog_name="Claude Code Telegram Bot")
@click.pass_context
def cli(
    ctx: click.Context,
    directory: Optional[Path],
    debug: bool,
    config_file: Optional[Path],
) -> None:
    """Claude Code Telegram Bot - AI-powered development assistant.

    Start the bot from any directory to use that directory as the
    approved working directory for file operations.

    \b
    Examples:
        # Start bot using current directory
        claude-telegram-bot

        # Start bot with specific directory
        claude-telegram-bot --directory /path/to/project

        # Enable debug logging
        claude-telegram-bot --debug
    """
    # If no subcommand, run the start command
    if ctx.invoked_subcommand is None:
        ctx.invoke(
            start,
            directory=directory,
            debug=debug,
            config_file=config_file,
        )


@cli.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=False, path_type=Path),
    default=None,
    help="Working directory for the bot (defaults to current directory)",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Enable debug logging",
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to configuration file",
)
def start(
    directory: Optional[Path],
    debug: bool,
    config_file: Optional[Path],
) -> None:
    """Start the Telegram bot.

    Uses the current directory as the approved directory for file operations
    unless --directory is specified.
    """
    # Determine working directory
    if directory is None:
        directory = Path.cwd().resolve()
    else:
        directory = directory.resolve()

    # Validate directory
    is_valid, error_msg = validate_directory(directory)
    if not is_valid:
        display_error(
            title="Invalid directory",
            message=error_msg,
            hint="Specify a valid directory with --directory",
        )
        sys.exit(1)

    # Set environment variables before loading config
    os.environ["APPROVED_DIRECTORY"] = str(directory)

    # Load .env from the specified directory
    env_file = directory / ".env"
    if env_file.exists():
        from dotenv import load_dotenv

        load_dotenv(env_file, override=True)

    # Validate configuration
    is_valid, error_msg, fix_steps = validate_config(directory)
    if not is_valid:
        display_error(
            title="Missing required configuration",
            message=error_msg,
            fix_steps=fix_steps,
            hint="Get a token from @BotFather on Telegram",
        )
        sys.exit(1)

    # Run the bot
    try:
        asyncio.run(run_bot(directory, debug, config_file))
    except KeyboardInterrupt:
        display_shutdown()
        sys.exit(0)
    except Exception as e:
        display_error(
            title="Runtime error",
            message=str(e),
            hint="Check the logs for more details or run with --debug",
        )
        sys.exit(2)


async def run_bot(
    directory: Path,
    debug: bool,
    config_file: Optional[Path],
) -> None:
    """Run the bot with the specified configuration.

    Args:
        directory: Working directory for the bot
        debug: Whether to enable debug logging
        config_file: Optional path to config file
    """
    from src.config import FeatureFlags, load_config
    from src.main import (
        create_application,
        run_application,
        setup_logging,
    )

    # Setup logging
    setup_logging(debug=debug)

    # Load configuration
    config = load_config(config_file=config_file)
    features = FeatureFlags(config)

    # Display startup banner
    enabled_features = features.get_enabled_features()
    bot_username = config.telegram_bot_username or "unknown"

    display_banner(
        bot_username=bot_username,
        approved_directory=str(directory),
        features=enabled_features,
        status="Starting...",
    )

    # Create and run application
    app = await create_application(config)

    # Update banner with Ready status after successful creation
    display_banner(
        bot_username=bot_username,
        approved_directory=str(directory),
        features=enabled_features,
        status="Ready",
    )

    await run_application(app)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
