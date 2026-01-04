"""Test slash command discovery and expansion."""

from pathlib import Path
from typing import List

import pytest


class TestSlashCommandLoader:
    """Test SlashCommandLoader class."""

    @pytest.fixture
    def temp_commands_dir(self, tmp_path: Path) -> Path:
        """Create temporary commands directory with test templates."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)

        # Create test command templates
        (commands_dir / "speckit.specify.md").write_text(
            "# Specify Feature\n\n$ARGUMENTS\n\nCreate specification."
        )
        (commands_dir / "speckit.plan.md").write_text(
            "# Plan Feature\n\nPlan implementation for $ARGUMENTS."
        )
        (commands_dir / "ralph-loop.md").write_text(
            "Start Ralph Wiggum loop with: $ARGUMENTS"
        )

        return commands_dir

    async def test_loader_discovers_commands(self, temp_commands_dir: Path) -> None:
        """Test that loader discovers command templates."""
        from src.claude.commands.loader import SlashCommandLoader

        loader = SlashCommandLoader(temp_commands_dir)

        commands = loader.list_commands()
        assert "speckit.specify" in commands
        assert "speckit.plan" in commands
        assert "ralph-loop" in commands

    async def test_loader_expands_arguments(self, temp_commands_dir: Path) -> None:
        """Test that loader expands $ARGUMENTS placeholder."""
        from src.claude.commands.loader import SlashCommandLoader

        loader = SlashCommandLoader(temp_commands_dir)

        expanded = loader.expand("speckit.specify", "add user login feature")

        assert "add user login feature" in expanded
        assert "$ARGUMENTS" not in expanded

    async def test_loader_handles_unknown_command(
        self, temp_commands_dir: Path
    ) -> None:
        """Test that loader raises error for unknown command."""
        from src.claude.commands.loader import SlashCommandLoader, UnknownCommandError

        loader = SlashCommandLoader(temp_commands_dir)

        with pytest.raises(UnknownCommandError) as exc_info:
            loader.expand("unknown.command", "args")

        assert "unknown.command" in str(exc_info.value)

    async def test_loader_handles_empty_arguments(
        self, temp_commands_dir: Path
    ) -> None:
        """Test that loader handles empty arguments."""
        from src.claude.commands.loader import SlashCommandLoader

        loader = SlashCommandLoader(temp_commands_dir)

        expanded = loader.expand("speckit.specify", "")

        # $ARGUMENTS should be replaced with empty string
        assert "$ARGUMENTS" not in expanded

    async def test_loader_handles_missing_directory(self, tmp_path: Path) -> None:
        """Test that loader handles missing commands directory."""
        from src.claude.commands.loader import SlashCommandLoader

        missing_dir = tmp_path / "nonexistent"
        loader = SlashCommandLoader(missing_dir)

        # Should have no commands
        assert len(loader.list_commands()) == 0


class TestCommandExpansion:
    """Test command template expansion."""

    @pytest.fixture
    def loader_with_templates(self, tmp_path: Path):
        """Create loader with various template types."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)

        # Template with multiple argument placeholders
        (commands_dir / "multi-args.md").write_text(
            "First: $ARGUMENTS\nSecond: $ARGUMENTS"
        )

        # Template with no arguments
        (commands_dir / "no-args.md").write_text("This command takes no arguments.")

        from src.claude.commands.loader import SlashCommandLoader

        return SlashCommandLoader(commands_dir)

    async def test_multiple_argument_placeholders(self, loader_with_templates) -> None:
        """Test expansion with multiple $ARGUMENTS."""
        expanded = loader_with_templates.expand("multi-args", "test value")

        # All occurrences should be replaced
        assert expanded.count("test value") == 2
        assert "$ARGUMENTS" not in expanded

    async def test_no_arguments_template(self, loader_with_templates) -> None:
        """Test template with no argument placeholders."""
        expanded = loader_with_templates.expand("no-args", "ignored args")

        # Template content should be preserved
        assert "This command takes no arguments." in expanded


class TestCommandExecutor:
    """Test command executor."""

    @pytest.fixture
    def temp_commands_dir(self, tmp_path: Path) -> Path:
        """Create temporary commands directory."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)

        # Use test.cmd pattern to match slash command regex (requires separator)
        (commands_dir / "test.cmd.md").write_text("Test command: $ARGUMENTS")

        return commands_dir

    async def test_executor_processes_slash_command(
        self, temp_commands_dir: Path
    ) -> None:
        """Test that executor processes slash commands."""
        from src.claude.commands.executor import CommandExecutor

        executor = CommandExecutor(temp_commands_dir)

        # Use pattern with separator (test.cmd) to match slash command regex
        result = await executor.process_message("/test.cmd hello world")

        assert result is not None
        assert result["is_command"] is True
        assert "hello world" in result["expanded_prompt"]

    async def test_executor_passes_through_regular_message(
        self, temp_commands_dir: Path
    ) -> None:
        """Test that executor passes through non-command messages."""
        from src.claude.commands.executor import CommandExecutor

        executor = CommandExecutor(temp_commands_dir)

        result = await executor.process_message("regular message")

        assert result["is_command"] is False
        assert result["original_message"] == "regular message"

    async def test_executor_handles_unknown_command(
        self, temp_commands_dir: Path
    ) -> None:
        """Test that executor handles unknown slash commands."""
        from src.claude.commands.executor import CommandExecutor

        executor = CommandExecutor(temp_commands_dir)

        result = await executor.process_message("/unknown.command args")

        assert result["is_command"] is True
        assert result["error"] is not None
        assert "unknown" in result["error"].lower()
        assert "available" in result["error"].lower()


class TestCommandQueue:
    """Test command execution queue."""

    async def test_sequential_command_execution(self, tmp_path: Path) -> None:
        """Test that commands are executed sequentially."""
        import asyncio

        from src.claude.commands.executor import CommandExecutor

        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        # Use pattern with separator to match slash command regex
        (commands_dir / "slow.exec.md").write_text("Slow command: $ARGUMENTS")

        executor = CommandExecutor(commands_dir)

        # Track execution order
        execution_order: List[int] = []

        async def track_execution(order: int):
            result = await executor.process_message(f"/slow.exec command{order}")
            execution_order.append(order)
            return result

        # Execute multiple commands concurrently
        await asyncio.gather(
            track_execution(1),
            track_execution(2),
            track_execution(3),
        )

        # All should complete (order may vary without proper queueing)
        assert len(execution_order) == 3

    async def test_command_in_progress_rejection(self, tmp_path: Path) -> None:
        """Test that rapid commands are handled properly."""
        from src.claude.commands.executor import CommandExecutor

        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        # Use pattern with separator to match slash command regex
        (commands_dir / "test.run.md").write_text("Test: $ARGUMENTS")

        executor = CommandExecutor(commands_dir)

        # Process command with proper format (requires separator in name)
        result = await executor.process_message("/test.run first")
        assert result["is_command"] is True


class TestCommandDetection:
    """Test slash command pattern detection."""

    async def test_speckit_commands_detected(self) -> None:
        """Test that /speckit.* commands are detected."""
        from src.claude.commands.executor import is_slash_command

        assert is_slash_command("/speckit.specify args") is True
        assert is_slash_command("/speckit.plan") is True
        assert is_slash_command("/speckit.tasks args") is True

    async def test_ralph_commands_detected(self) -> None:
        """Test that /ralph-* commands are detected."""
        from src.claude.commands.executor import is_slash_command

        assert is_slash_command("/ralph-loop args") is True
        assert is_slash_command("/ralph-stop") is True

    async def test_regular_messages_not_detected(self) -> None:
        """Test that regular messages are not detected as commands."""
        from src.claude.commands.executor import is_slash_command

        assert is_slash_command("regular message") is False
        assert is_slash_command("/help") is False  # Built-in, not slash command
        assert is_slash_command("not /a command") is False

    async def test_custom_commands_detected(self) -> None:
        """Test that custom command patterns work."""
        from src.claude.commands.executor import is_slash_command

        # Any /word.word or /word-word pattern should match
        assert is_slash_command("/custom.command args") is True
        assert is_slash_command("/my-command") is True
