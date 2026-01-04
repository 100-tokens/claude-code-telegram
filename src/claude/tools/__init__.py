"""Custom in-process MCP tools for Telegram integration.

This module provides Telegram-specific tools that Claude can use
to send rich responses (keyboards, files, progress updates).
"""

from .registry import (
    ToolRegistry,
    get_registry,
    register_tool,
    safe_tool_execution,
)
from .telegram_tools import (
    TelegramToolContext,
    get_telegram_context,
    get_telegram_tools,
    set_telegram_context,
    telegram_file,
    telegram_keyboard,
    telegram_message,
    telegram_progress,
)

__all__ = [
    # Registry
    "ToolRegistry",
    "get_registry",
    "register_tool",
    "safe_tool_execution",
    # Telegram tools
    "telegram_keyboard",
    "telegram_file",
    "telegram_progress",
    "telegram_message",
    "get_telegram_tools",
    # Context
    "TelegramToolContext",
    "set_telegram_context",
    "get_telegram_context",
]
