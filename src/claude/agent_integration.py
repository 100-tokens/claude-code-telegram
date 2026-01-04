"""Claude Agent SDK Integration.

This module provides the AgentIntegration class that wraps the Claude Agent SDK
for bidirectional, stateful conversations with custom tools and security hooks.

Features:
- ClaudeSDKClient lifecycle management per user
- Custom Telegram tool registration via MCP servers
- Security hooks for permission control (PreToolUse)
- Bidirectional conversation state with async streaming
- Tool execution timeout handling
"""

import asyncio
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import structlog

from src.config.settings import Settings

from .exceptions import (
    ClaudeTimeoutError,
)

logger = structlog.get_logger(__name__)

# Try to import from new SDK, fall back to old SDK
SDK_AVAILABLE = False
SDK_TYPE = "none"

try:
    from claude_agent_sdk import (
        CLIJSONDecodeError,
        CLINotFoundError,
        ClaudeAgentOptions,
        ClaudeSDKClient,
        ProcessError,
    )

    SDK_AVAILABLE = True
    SDK_TYPE = "agent"
    logger.info("Using claude-agent-sdk")
except ImportError:
    try:
        from claude_code_sdk import (
            ClaudeCodeOptions,
            CLINotFoundError,
            ProcessError,
        )
        from claude_code_sdk import query as sdk_query

        SDK_AVAILABLE = True
        SDK_TYPE = "code"
        logger.info("Falling back to claude-code-sdk")
    except ImportError:
        logger.warning("No Claude SDK available - running in stub mode")


@dataclass
class AgentResponse:
    """Response from Claude Agent SDK."""

    content: str
    session_id: str
    cost: float
    duration_ms: int
    num_turns: int
    is_error: bool = False
    error_type: Optional[str] = None
    tools_used: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StreamUpdate:
    """Streaming update from Agent SDK."""

    type: str  # 'text', 'tool_use', 'tool_result', 'error', 'complete'
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentIntegration:
    """Wrapper for Claude Agent SDK with Telegram-specific tools and hooks.

    This class manages:
    - ClaudeSDKClient lifecycle per user
    - Custom Telegram tool registration
    - Security hooks for permission control
    - Bidirectional conversation state
    - Tool execution timeouts
    """

    def __init__(
        self,
        config: Settings,
        telegram_context: Optional[Any] = None,
    ) -> None:
        """Initialize the agent integration.

        Args:
            config: Application settings with SDK configuration
            telegram_context: Telegram bot context for tool callbacks
        """
        self.config = config
        self.telegram_context = telegram_context
        self.clients: Dict[int, Any] = {}  # user_id -> ClaudeSDKClient or session data
        self._options: Optional[Any] = None
        self._initialized = False

        # Set up environment for API key if provided
        if config.anthropic_api_key_str:
            os.environ["ANTHROPIC_API_KEY"] = config.anthropic_api_key_str
            logger.info("Using provided API key for Claude SDK authentication")

    async def initialize(self) -> None:
        """Initialize the SDK and create options."""
        if self._initialized:
            return

        logger.info(
            "Initializing Claude Agent SDK integration",
            sdk_type=SDK_TYPE,
            sdk_available=SDK_AVAILABLE,
        )

        if SDK_AVAILABLE:
            self._options = self._create_options()

        self._initialized = True

    def _create_options(self) -> Any:
        """Create ClaudeAgentOptions with tools and hooks.

        Returns:
            Configured ClaudeAgentOptions or ClaudeCodeOptions instance
        """
        if SDK_TYPE == "agent":
            # New claude-agent-sdk
            mcp_servers = {}
            hooks = {}

            if self.config.enable_telegram_tools:
                mcp_servers = self._create_mcp_servers()

            if self.config.enable_security_hooks:
                hooks = self._create_security_hooks()

            return ClaudeAgentOptions(
                max_turns=self.config.claude_max_turns,
                allowed_tools=self.config.claude_allowed_tools,
                permission_mode=self.config.permission_mode,
                cwd=str(self.config.approved_directory),
                mcp_servers=mcp_servers,
                hooks=hooks,
            )

        elif SDK_TYPE == "code":
            # Old claude-code-sdk fallback
            return ClaudeCodeOptions(
                max_turns=self.config.claude_max_turns,
                cwd=str(self.config.approved_directory),
                allowed_tools=self.config.claude_allowed_tools,
            )

        return None

    def _create_mcp_servers(self) -> Dict[str, Any]:
        """Create MCP servers for Telegram tools.

        Returns:
            Dictionary of MCP server configurations
        """
        if not self.config.enable_telegram_tools:
            return {}

        try:
            # Import telegram_tools to trigger tool registration via @register_tool
            from .tools import telegram_tools  # noqa: F401
            from .tools.registry import get_registry

            registry = get_registry()
            return registry.get_mcp_server_config()

        except ImportError as e:
            logger.warning("Failed to load Telegram tools", error=str(e))
            return {}

    def _create_security_hooks(self) -> Dict[str, Any]:
        """Create security hooks for permission control.

        Returns:
            Dictionary of hook configurations
        """
        if not self.config.enable_security_hooks:
            return {}

        try:
            from .hooks.security_hooks import create_security_hooks

            hooks = create_security_hooks()
            logger.info(
                "Registered security hooks",
                hook_count=len(hooks.get("PreToolUse", [])),
            )
            return hooks
        except ImportError as e:
            logger.warning("Failed to load security hooks", error=str(e))
            return {}

    async def _get_client(self, user_id: int) -> Any:
        """Get or create a ClaudeSDKClient for the user.

        Args:
            user_id: Telegram user ID

        Returns:
            ClaudeSDKClient instance or session data for the user
        """
        if user_id not in self.clients:
            if SDK_TYPE == "agent":
                # New SDK: create ClaudeSDKClient
                client = ClaudeSDKClient(options=self._options)
                await client.__aenter__()
                self.clients[user_id] = client
                logger.info("Created new Agent SDK client", user_id=user_id)
            else:
                # Old SDK or stub: use session dictionary
                self.clients[user_id] = {
                    "session_id": str(uuid.uuid4()),
                    "messages": [],
                    "created_at": asyncio.get_event_loop().time(),
                }
                logger.info("Created new session", user_id=user_id)

        return self.clients.get(user_id)

    async def query(
        self,
        user_id: int,
        prompt: str,
        stream_callback: Optional[Callable[[StreamUpdate], Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Send a query and stream responses.

        Args:
            user_id: Telegram user ID
            prompt: User's message to Claude
            stream_callback: Optional callback for streaming updates

        Yields:
            Response messages from Claude
        """
        if not self._initialized:
            await self.initialize()

        start_time = asyncio.get_event_loop().time()

        try:
            if SDK_TYPE == "agent":
                async for response in self._query_agent_sdk(
                    user_id, prompt, stream_callback
                ):
                    yield response
            elif SDK_TYPE == "code":
                async for response in self._query_code_sdk(
                    user_id, prompt, stream_callback
                ):
                    yield response
            else:
                # Stub mode
                yield {
                    "type": "text",
                    "content": f"[SDK stub] No SDK available. Received: {prompt}",
                }

        except asyncio.TimeoutError:
            duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            logger.error(
                "Query timed out",
                user_id=user_id,
                timeout=self.config.claude_timeout_seconds,
                duration_ms=duration_ms,
            )
            yield {
                "type": "error",
                "content": f"Request timed out after {self.config.claude_timeout_seconds}s",
                "error_type": "timeout",
            }

        except Exception as e:
            duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            error_type = type(e).__name__
            logger.error(
                "Query failed",
                user_id=user_id,
                error=str(e),
                error_type=error_type,
                duration_ms=duration_ms,
            )
            yield {
                "type": "error",
                "content": self._format_error_message(e),
                "error_type": error_type,
            }

    async def _query_agent_sdk(
        self,
        user_id: int,
        prompt: str,
        stream_callback: Optional[Callable[[StreamUpdate], Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Query using claude-agent-sdk (ClaudeSDKClient).

        Args:
            user_id: Telegram user ID
            prompt: User's message
            stream_callback: Optional streaming callback

        Yields:
            Response messages
        """
        client = await self._get_client(user_id)

        # Apply timeout to entire query
        try:
            await asyncio.wait_for(
                client.query(prompt),
                timeout=self.config.claude_timeout_seconds,
            )
        except asyncio.TimeoutError:
            raise ClaudeTimeoutError(
                f"Query timed out after {self.config.claude_timeout_seconds}s"
            )

        # Stream responses with tool timeout
        async for msg in client.receive_response():
            # Apply tool timeout for tool executions
            if hasattr(msg, "tool_use"):
                try:
                    await asyncio.wait_for(
                        self._handle_tool_with_timeout(msg),
                        timeout=self.config.tool_timeout_seconds,
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "Tool execution timed out",
                        user_id=user_id,
                        timeout=self.config.tool_timeout_seconds,
                    )
                    yield {
                        "type": "error",
                        "content": f"Tool execution timed out after {self.config.tool_timeout_seconds}s",
                        "error_type": "tool_timeout",
                    }
                    continue

            # Convert to dict format
            response = self._convert_message_to_dict(msg)

            # Call streaming callback if provided
            if stream_callback and response:
                update = StreamUpdate(
                    type=response.get("type", "text"),
                    content=response.get("content"),
                    tool_name=response.get("tool_name"),
                    tool_input=response.get("tool_input"),
                )
                try:
                    result = stream_callback(update)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.warning("Stream callback failed", error=str(e))

            if response:
                yield response

    async def _handle_tool_with_timeout(self, msg: Any) -> None:
        """Handle tool execution with timeout.

        Args:
            msg: Message with tool use
        """
        # Placeholder for tool execution handling
        # The actual tool execution is handled by the SDK
        pass

    async def _query_code_sdk(
        self,
        user_id: int,
        prompt: str,
        stream_callback: Optional[Callable[[StreamUpdate], Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Query using legacy claude-code-sdk.

        Args:
            user_id: Telegram user ID
            prompt: User's message
            stream_callback: Optional streaming callback

        Yields:
            Response messages
        """
        session_data = await self._get_client(user_id)
        content_parts = []
        tools_used = []

        try:
            async for message in asyncio.wait_for(
                self._execute_code_sdk_query(prompt),
                timeout=self.config.claude_timeout_seconds,
            ):
                # Handle AssistantMessage
                if hasattr(message, "content"):
                    msg_content = getattr(message, "content", [])
                    if isinstance(msg_content, list):
                        for block in msg_content:
                            if hasattr(block, "text"):
                                text = block.text
                                content_parts.append(text)
                                if stream_callback:
                                    update = StreamUpdate(type="text", content=text)
                                    try:
                                        result = stream_callback(update)
                                        if asyncio.iscoroutine(result):
                                            await result
                                    except Exception as e:
                                        logger.warning(
                                            "Stream callback failed", error=str(e)
                                        )
                                yield {"type": "text", "content": text}

                            elif hasattr(block, "tool_name"):
                                tool_info = {
                                    "name": getattr(block, "tool_name", "unknown"),
                                    "input": getattr(block, "tool_input", {}),
                                }
                                tools_used.append(tool_info)
                                yield {
                                    "type": "tool_use",
                                    "tool_name": tool_info["name"],
                                    "tool_input": tool_info["input"],
                                }

                # Handle ResultMessage
                if hasattr(message, "total_cost_usd"):
                    yield {
                        "type": "complete",
                        "content": "\n".join(content_parts),
                        "cost": getattr(message, "total_cost_usd", 0.0),
                        "session_id": session_data.get("session_id", ""),
                        "tools_used": tools_used,
                    }

        except asyncio.TimeoutError:
            raise ClaudeTimeoutError(
                f"Query timed out after {self.config.claude_timeout_seconds}s"
            )

    async def _execute_code_sdk_query(self, prompt: str) -> AsyncIterator[Any]:
        """Execute query with legacy claude-code-sdk.

        Args:
            prompt: User prompt

        Yields:
            SDK messages
        """
        async for msg in sdk_query(prompt=prompt, options=self._options):
            yield msg

    def _convert_message_to_dict(self, msg: Any) -> Optional[Dict[str, Any]]:
        """Convert SDK message to dictionary format.

        Args:
            msg: SDK message object

        Returns:
            Dictionary representation or None
        """
        if msg is None:
            return None

        result: Dict[str, Any] = {}

        # Handle text content
        if hasattr(msg, "content"):
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                result["type"] = "text"
                result["content"] = content
            elif isinstance(content, list):
                texts = []
                for block in content:
                    if hasattr(block, "text"):
                        texts.append(block.text)
                if texts:
                    result["type"] = "text"
                    result["content"] = "\n".join(texts)

        # Handle tool use
        if hasattr(msg, "tool_use"):
            result["type"] = "tool_use"
            result["tool_name"] = getattr(msg.tool_use, "name", "unknown")
            result["tool_input"] = getattr(msg.tool_use, "input", {})

        # Handle result/completion
        if hasattr(msg, "total_cost_usd"):
            result["type"] = "complete"
            result["cost"] = getattr(msg, "total_cost_usd", 0.0)
            result["session_id"] = getattr(msg, "session_id", "")

        return result if result else None

    def _format_error_message(self, error: Exception) -> str:
        """Format error into user-friendly message.

        Args:
            error: Exception to format

        Returns:
            Formatted error message
        """
        error_type = type(error).__name__

        if SDK_AVAILABLE and SDK_TYPE == "agent":
            if isinstance(error, CLINotFoundError):
                return (
                    "Claude CLI not found. Please ensure Claude is installed:\n"
                    "  npm install -g @anthropic-ai/claude-code"
                )
            elif isinstance(error, ProcessError):
                return f"Claude process error: {str(error)}"
            elif isinstance(error, CLIJSONDecodeError):
                return f"Failed to parse Claude response: {str(error)}"

        elif SDK_AVAILABLE and SDK_TYPE == "code":
            if isinstance(error, CLINotFoundError):
                return (
                    "Claude CLI not found. Please ensure Claude is installed:\n"
                    "  npm install -g @anthropic-ai/claude-code"
                )
            elif isinstance(error, ProcessError):
                return f"Claude process error: {str(error)}"

        return f"Error ({error_type}): {str(error)}"

    async def close_session(self, user_id: int) -> None:
        """Close a user's session and cleanup resources.

        Args:
            user_id: Telegram user ID
        """
        if user_id in self.clients:
            client = self.clients.pop(user_id)

            if SDK_TYPE == "agent" and hasattr(client, "__aexit__"):
                try:
                    await client.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning("Error closing SDK client", error=str(e))

            logger.info("Closed SDK client session", user_id=user_id)

    async def close_all(self) -> None:
        """Close all active sessions concurrently."""
        user_ids = list(self.clients.keys())
        if user_ids:
            # Close all sessions concurrently for faster shutdown
            await asyncio.gather(
                *(self.close_session(uid) for uid in user_ids),
                return_exceptions=True,
            )
        logger.info("Closed all SDK client sessions", count=len(user_ids))

    def get_active_session_count(self) -> int:
        """Get number of active sessions.

        Returns:
            Number of active user sessions
        """
        return len(self.clients)

    @property
    def is_sdk_available(self) -> bool:
        """Check if any SDK is available.

        Returns:
            True if SDK is available
        """
        return SDK_AVAILABLE

    @property
    def sdk_type(self) -> str:
        """Get the type of SDK being used.

        Returns:
            SDK type: 'agent', 'code', or 'none'
        """
        return SDK_TYPE
