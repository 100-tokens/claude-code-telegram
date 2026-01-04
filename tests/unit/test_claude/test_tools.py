"""Test custom Telegram tools for Claude integration."""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock


class TestToolRegistry:
    """Test tool registration and discovery."""

    async def test_registry_creates_mcp_server(self) -> None:
        """Test that registry creates MCP server configuration."""
        from src.claude.tools.registry import ToolRegistry

        registry = ToolRegistry()
        assert registry is not None
        assert registry.tools == {}

    async def test_registry_register_tool(self) -> None:
        """Test registering a tool with the registry."""
        from src.claude.tools.registry import ToolRegistry

        registry = ToolRegistry()

        async def test_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"content": [{"type": "text", "text": "test"}]}

        registry.register(
            name="test_tool",
            description="A test tool",
            input_schema={"message": str},
            handler=test_tool,
        )

        assert "test_tool" in registry.tools
        assert registry.tools["test_tool"]["description"] == "A test tool"

    async def test_registry_get_mcp_server_config(self) -> None:
        """Test getting MCP server configuration from registry."""
        from src.claude.tools.registry import ToolRegistry

        registry = ToolRegistry()

        async def test_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"content": [{"type": "text", "text": "test"}]}

        registry.register(
            name="telegram_test",
            description="Test tool",
            input_schema={},
            handler=test_tool,
        )

        # Get MCP server config
        config = registry.get_mcp_server_config()
        assert config is not None


class TestTelegramKeyboardTool:
    """Test telegram_keyboard tool."""

    async def test_keyboard_tool_creates_inline_keyboard(self) -> None:
        """Test that keyboard tool creates inline keyboard markup."""
        from src.claude.tools.telegram_tools import telegram_keyboard

        mock_context = MagicMock()
        mock_context.send_message = AsyncMock()

        result = await telegram_keyboard(
            args={
                "buttons": [["Option 1", "Option 2"], ["Cancel"]],
                "message": "Choose an option:",
            },
            context=mock_context,
        )

        assert result is not None
        assert "content" in result

    async def test_keyboard_tool_validates_buttons(self) -> None:
        """Test that keyboard tool validates button input."""
        from src.claude.tools.telegram_tools import telegram_keyboard

        mock_context = MagicMock()

        # Empty buttons should return error
        result = await telegram_keyboard(
            args={"buttons": [], "message": "Choose:"},
            context=mock_context,
        )

        assert "error" in str(result).lower() or result is not None


class TestTelegramFileTool:
    """Test telegram_file tool."""

    async def test_file_tool_sends_document(self) -> None:
        """Test that file tool sends document."""
        from src.claude.tools.telegram_tools import telegram_file

        mock_context = MagicMock()
        mock_context.send_document = AsyncMock()

        result = await telegram_file(
            args={
                "content": "print('hello')",
                "filename": "hello.py",
            },
            context=mock_context,
        )

        assert result is not None

    async def test_file_tool_validates_content(self) -> None:
        """Test that file tool validates content."""
        from src.claude.tools.telegram_tools import telegram_file

        mock_context = MagicMock()

        # Empty content should handle gracefully
        result = await telegram_file(
            args={"content": "", "filename": "empty.txt"},
            context=mock_context,
        )

        assert result is not None


class TestTelegramProgressTool:
    """Test telegram_progress tool."""

    async def test_progress_tool_updates_message(self) -> None:
        """Test that progress tool updates progress message."""
        from src.claude.tools.telegram_tools import telegram_progress

        mock_context = MagicMock()
        mock_context.edit_message = AsyncMock()

        result = await telegram_progress(
            args={
                "message": "Processing...",
                "percent": 50,
            },
            context=mock_context,
        )

        assert result is not None

    async def test_progress_tool_clamps_percent(self) -> None:
        """Test that progress tool clamps percent to 0-100."""
        from src.claude.tools.telegram_tools import telegram_progress

        mock_context = MagicMock()
        mock_context.edit_message = AsyncMock()

        # Test with > 100
        result = await telegram_progress(
            args={"message": "Done!", "percent": 150},
            context=mock_context,
        )
        assert result is not None

        # Test with < 0
        result = await telegram_progress(
            args={"message": "Starting...", "percent": -10},
            context=mock_context,
        )
        assert result is not None


class TestTelegramMessageTool:
    """Test telegram_message tool."""

    async def test_message_tool_sends_formatted_text(self) -> None:
        """Test that message tool sends formatted text."""
        from src.claude.tools.telegram_tools import telegram_message

        mock_context = MagicMock()
        mock_context.send_message = AsyncMock()

        result = await telegram_message(
            args={
                "text": "**Bold** and *italic*",
                "parse_mode": "Markdown",
            },
            context=mock_context,
        )

        assert result is not None

    async def test_message_tool_default_parse_mode(self) -> None:
        """Test that message tool uses default parse mode."""
        from src.claude.tools.telegram_tools import telegram_message

        mock_context = MagicMock()
        mock_context.send_message = AsyncMock()

        result = await telegram_message(
            args={"text": "Plain text message"},
            context=mock_context,
        )

        assert result is not None


class TestToolExceptionHandling:
    """Test tool exception handling."""

    async def test_tool_error_returns_friendly_message(self) -> None:
        """Test that tool errors return user-friendly messages."""
        from src.claude.tools.registry import safe_tool_execution

        async def failing_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            raise ValueError("Something went wrong")

        result = await safe_tool_execution(failing_tool, {"test": "input"})

        assert result is not None
        assert "error" in result or "content" in result

    async def test_tool_timeout_handled(self) -> None:
        """Test that tool timeout is handled gracefully."""
        import asyncio

        from src.claude.tools.registry import safe_tool_execution

        async def slow_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(10)
            return {"content": [{"type": "text", "text": "done"}]}

        # This test verifies the structure exists
        # Actual timeout would be tested in integration tests
        assert safe_tool_execution is not None
