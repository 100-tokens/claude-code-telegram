"""Display utilities for CLI output formatting.

Provides functions for displaying startup banners, error messages,
and shutdown confirmations with consistent formatting.
"""

import click

from src import __version__


def display_banner(
    bot_username: str,
    approved_directory: str,
    features: list[str],
    status: str = "Ready",
) -> None:
    """Display the startup banner with bot information.

    Args:
        bot_username: The Telegram bot username
        approved_directory: The directory the bot is operating in
        features: List of enabled features
        status: Current bot status (default: "Ready")
    """
    # Box drawing characters for nice formatting
    width = 65

    click.echo()
    click.echo(click.style("╭" + "─" * width + "╮", fg="cyan"))
    click.echo(
        click.style("│", fg="cyan")
        + f"  Claude Code Telegram Bot v{__version__}".ljust(width)
        + click.style("│", fg="cyan")
    )
    click.echo(click.style("├" + "─" * width + "┤", fg="cyan"))

    # Bot username
    click.echo(
        click.style("│", fg="cyan")
        + f"  Bot:       @{bot_username}".ljust(width)
        + click.style("│", fg="cyan")
    )

    # Approved directory (truncate if too long)
    dir_display = approved_directory
    if len(dir_display) > 50:
        dir_display = "..." + dir_display[-47:]
    click.echo(
        click.style("│", fg="cyan")
        + f"  Directory: {dir_display}".ljust(width)
        + click.style("│", fg="cyan")
    )

    # Features
    features_str = ", ".join(features) if features else "None"
    click.echo(
        click.style("│", fg="cyan")
        + f"  Features:  {features_str}".ljust(width)
        + click.style("│", fg="cyan")
    )

    # Status with color
    status_color = "green" if status == "Ready" else "yellow"
    status_line = f"  Status:    {status}"
    click.echo(
        click.style("│", fg="cyan")
        + click.style(status_line, fg=status_color).ljust(
            width + 9
        )  # +9 for ANSI codes
        + click.style("│", fg="cyan")
    )

    click.echo(click.style("╰" + "─" * width + "╯", fg="cyan"))
    click.echo()


def display_error(
    title: str,
    message: str,
    fix_steps: list[str] | None = None,
    hint: str | None = None,
) -> None:
    """Display a formatted error message with optional fix guidance.

    Args:
        title: Short error title
        message: Detailed error message
        fix_steps: Optional list of steps to fix the issue
        hint: Optional additional hint
    """
    click.echo()
    click.echo(click.style(f"Error: {title}", fg="red", bold=True))
    click.echo()
    click.echo(f"  {message}")

    if fix_steps:
        click.echo()
        click.echo(click.style("To fix:", fg="yellow"))
        for i, step in enumerate(fix_steps, 1):
            click.echo(f"  {i}. {step}")

    if hint:
        click.echo()
        click.echo(click.style(hint, fg="bright_black"))

    click.echo()


def display_shutdown(sessions_closed: int = 0) -> None:
    """Display shutdown confirmation message.

    Args:
        sessions_closed: Number of sessions that were closed
    """
    click.echo()
    click.echo(click.style("Shutting down...", fg="yellow"))
    if sessions_closed > 0:
        click.echo(f"  Sessions closed: {sessions_closed}")
    click.echo("  Cleanup complete")
    click.echo(click.style("Goodbye!", fg="green"))
    click.echo()
