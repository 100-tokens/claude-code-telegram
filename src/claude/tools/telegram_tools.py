"""Custom Telegram tools for Claude Agent SDK.

These tools enable Claude to send rich Telegram responses including
inline keyboards, file attachments, progress updates, and formatted messages.
"""

import contextvars
import io
from typing import Any, Dict, List, Optional, Union

import structlog

from .registry import register_tool

logger = structlog.get_logger(__name__)


class TelegramToolContext:
    """Context for Telegram tool execution.

    Provides access to Telegram bot methods for sending messages,
    files, keyboards, and editing messages.
    """

    def __init__(
        self,
        chat_id: int,
        message_id: Optional[int] = None,
        bot: Optional[Any] = None,
    ) -> None:
        """Initialize Telegram context.

        Args:
            chat_id: Telegram chat ID
            message_id: Optional message ID for editing
            bot: Telegram bot instance
        """
        self.chat_id = chat_id
        self.message_id = message_id
        self.bot = bot

    async def send_message(
        self,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Any] = None,
    ) -> Optional[Any]:
        """Send a message to the chat.

        Args:
            text: Message text
            parse_mode: Parse mode (Markdown, HTML, etc.)
            reply_markup: Optional reply markup

        Returns:
            Sent message or None
        """
        if self.bot is None:
            logger.warning("No bot instance available")
            return None

        try:
            return await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        except Exception as e:
            logger.error("Failed to send message", error=str(e))
            return None

    async def send_document(
        self,
        document: Union[bytes, io.BytesIO],
        filename: str,
        caption: Optional[str] = None,
    ) -> Optional[Any]:
        """Send a document to the chat.

        Args:
            document: Document content
            filename: File name
            caption: Optional caption

        Returns:
            Sent message or None
        """
        if self.bot is None:
            logger.warning("No bot instance available")
            return None

        try:
            if isinstance(document, bytes):
                document = io.BytesIO(document)
                document.name = filename

            return await self.bot.send_document(
                chat_id=self.chat_id,
                document=document,
                filename=filename,
                caption=caption,
            )
        except Exception as e:
            logger.error("Failed to send document", error=str(e))
            return None

    async def edit_message(
        self,
        text: str,
        parse_mode: Optional[str] = None,
    ) -> Optional[Any]:
        """Edit an existing message.

        Args:
            text: New message text
            parse_mode: Parse mode

        Returns:
            Edited message or None
        """
        if self.bot is None or self.message_id is None:
            logger.warning("No bot or message_id available")
            return None

        try:
            return await self.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=text,
                parse_mode=parse_mode,
            )
        except Exception as e:
            logger.error("Failed to edit message", error=str(e))
            return None


# Thread-safe context storage using ContextVar (safe for async/concurrent requests)
_current_context: contextvars.ContextVar[Optional[TelegramToolContext]] = (
    contextvars.ContextVar("telegram_context", default=None)
)


def set_telegram_context(context: TelegramToolContext) -> None:
    """Set the current Telegram context for tool execution.

    Args:
        context: TelegramToolContext instance
    """
    _current_context.set(context)


def get_telegram_context() -> Optional[TelegramToolContext]:
    """Get the current Telegram context.

    Returns:
        Current context or None
    """
    return _current_context.get()


@register_tool(
    name="telegram_keyboard",
    description="Send an inline keyboard with clickable buttons to the user. Use this when you want to present options or choices.",
    input_schema={
        "type": "object",
        "properties": {
            "buttons": {
                "type": "array",
                "description": "2D array of button labels. Each inner array is a row.",
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "message": {
                "type": "string",
                "description": "Message to display with the keyboard",
            },
        },
        "required": ["buttons", "message"],
    },
)
async def telegram_keyboard(
    args: Dict[str, Any],
    context: Optional[TelegramToolContext] = None,
) -> Dict[str, Any]:
    """Send an inline keyboard to the user.

    Args:
        args: Tool arguments with buttons and message
        context: Optional Telegram context (uses global if not provided)

    Returns:
        Tool result
    """
    ctx = context or get_telegram_context()
    buttons = args.get("buttons", [])
    message = args.get("message", "")

    if not buttons:
        return {
            "content": [{"type": "text", "text": "Error: No buttons provided"}],
            "isError": True,
        }

    if not message:
        return {
            "content": [{"type": "text", "text": "Error: No message provided"}],
            "isError": True,
        }

    # Build keyboard markup
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = []
        for row in buttons:
            keyboard_row = []
            for btn_text in row:
                # Ensure callback_data is within 64 bytes (Telegram limit)
                # even with multi-byte characters like emojis
                cb_data = btn_text.encode("utf-8")[:64].decode("utf-8", "ignore")
                keyboard_row.append(
                    InlineKeyboardButton(btn_text, callback_data=cb_data)
                )
            keyboard.append(keyboard_row)

        reply_markup = InlineKeyboardMarkup(keyboard)

        if ctx:
            await ctx.send_message(message, reply_markup=reply_markup)
            logger.info("Sent keyboard", button_count=sum(len(r) for r in buttons))
        else:
            logger.warning("No context available, keyboard not sent")

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Keyboard sent with {sum(len(r) for r in buttons)} buttons",
                }
            ],
        }

    except ImportError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Keyboard prepared (telegram library not available)",
                }
            ],
        }
    except Exception as e:
        logger.error("Failed to send keyboard", error=str(e))
        return {
            "content": [{"type": "text", "text": f"Failed to send keyboard: {str(e)}"}],
            "isError": True,
        }


@register_tool(
    name="telegram_file",
    description="Send a file attachment to the user. Use this for code snippets, logs, or any content better viewed as a file.",
    input_schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "File content as text",
            },
            "filename": {
                "type": "string",
                "description": "File name with extension (e.g., 'code.py', 'log.txt')",
            },
            "caption": {
                "type": "string",
                "description": "Optional caption for the file",
            },
        },
        "required": ["content", "filename"],
    },
)
async def telegram_file(
    args: Dict[str, Any],
    context: Optional[TelegramToolContext] = None,
) -> Dict[str, Any]:
    """Send a file attachment to the user.

    Args:
        args: Tool arguments with content and filename
        context: Optional Telegram context

    Returns:
        Tool result
    """
    ctx = context or get_telegram_context()
    content = args.get("content", "")
    filename = args.get("filename", "file.txt")
    caption = args.get("caption")

    if not content:
        return {
            "content": [{"type": "text", "text": "Error: No file content provided"}],
            "isError": True,
        }

    try:
        # Create file buffer
        file_bytes = content.encode("utf-8")
        file_buffer = io.BytesIO(file_bytes)
        file_buffer.name = filename

        if ctx:
            await ctx.send_document(
                document=file_buffer,
                filename=filename,
                caption=caption,
            )
            logger.info("Sent file", filename=filename, size=len(file_bytes))
        else:
            logger.warning("No context available, file not sent")

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"File '{filename}' sent ({len(file_bytes)} bytes)",
                }
            ],
        }

    except Exception as e:
        logger.error("Failed to send file", error=str(e))
        return {
            "content": [{"type": "text", "text": f"Failed to send file: {str(e)}"}],
            "isError": True,
        }


@register_tool(
    name="telegram_progress",
    description="Update a progress message to show task completion status. Use this for long-running operations.",
    input_schema={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Progress message text",
            },
            "percent": {
                "type": "integer",
                "description": "Completion percentage (0-100)",
                "minimum": 0,
                "maximum": 100,
            },
        },
        "required": ["message", "percent"],
    },
)
async def telegram_progress(
    args: Dict[str, Any],
    context: Optional[TelegramToolContext] = None,
) -> Dict[str, Any]:
    """Update a progress message.

    Args:
        args: Tool arguments with message and percent
        context: Optional Telegram context

    Returns:
        Tool result
    """
    ctx = context or get_telegram_context()
    message = args.get("message", "Processing...")
    percent = args.get("percent", 0)

    # Clamp percent to 0-100
    percent = max(0, min(100, percent))

    # Create progress bar
    bar_length = 10
    filled = int(bar_length * percent / 100)
    bar = "█" * filled + "░" * (bar_length - filled)

    progress_text = f"{message}\n\n[{bar}] {percent}%"

    try:
        if ctx and ctx.message_id:
            await ctx.edit_message(progress_text)
            logger.info("Updated progress", percent=percent)
        elif ctx:
            await ctx.send_message(progress_text)
            logger.info("Sent progress message", percent=percent)
        else:
            logger.warning("No context available, progress not updated")

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Progress updated: {percent}%",
                }
            ],
        }

    except Exception as e:
        logger.error("Failed to update progress", error=str(e))
        return {
            "content": [
                {"type": "text", "text": f"Failed to update progress: {str(e)}"}
            ],
            "isError": True,
        }


@register_tool(
    name="telegram_message",
    description="Send a formatted message with Markdown or HTML formatting. Use this for rich text responses.",
    input_schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Message text with optional formatting",
            },
            "parse_mode": {
                "type": "string",
                "description": "Parse mode: 'Markdown', 'MarkdownV2', or 'HTML'",
                "enum": ["Markdown", "MarkdownV2", "HTML"],
            },
        },
        "required": ["text"],
    },
)
async def telegram_message(
    args: Dict[str, Any],
    context: Optional[TelegramToolContext] = None,
) -> Dict[str, Any]:
    """Send a formatted message.

    Args:
        args: Tool arguments with text and optional parse_mode
        context: Optional Telegram context

    Returns:
        Tool result
    """
    ctx = context or get_telegram_context()
    text = args.get("text", "")
    parse_mode = args.get("parse_mode", "Markdown")

    if not text:
        return {
            "content": [{"type": "text", "text": "Error: No message text provided"}],
            "isError": True,
        }

    try:
        if ctx:
            await ctx.send_message(text, parse_mode=parse_mode)
            logger.info(
                "Sent formatted message",
                parse_mode=parse_mode,
                length=len(text),
            )
        else:
            logger.warning("No context available, message not sent")

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Message sent ({len(text)} chars, {parse_mode})",
                }
            ],
        }

    except Exception as e:
        logger.error("Failed to send message", error=str(e))
        return {
            "content": [{"type": "text", "text": f"Failed to send message: {str(e)}"}],
            "isError": True,
        }


def get_telegram_tools() -> List[str]:
    """Get list of Telegram tool names.

    Returns:
        List of tool names
    """
    return [
        "telegram_keyboard",
        "telegram_file",
        "telegram_progress",
        "telegram_message",
    ]
