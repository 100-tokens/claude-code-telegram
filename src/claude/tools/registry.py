"""Tool registry for Claude Agent SDK MCP server integration.

This module provides a registry for custom tools and wraps them
for use with the Claude Agent SDK's MCP server system.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Type alias for tool handlers
ToolHandler = Callable[[Dict[str, Any]], Any]

# Try to import SDK components
SDK_AVAILABLE = False
try:
    from claude_agent_sdk import create_sdk_mcp_server
    from claude_agent_sdk import tool as sdk_tool

    SDK_AVAILABLE = True
except ImportError:
    logger.debug("claude-agent-sdk not available, using stub tool decorator")


def tool_decorator(name: str, description: str, input_schema: Dict[str, Any]):
    """Decorator for registering tools.

    Works with claude-agent-sdk when available, otherwise provides stub.

    Args:
        name: Tool name
        description: Tool description
        input_schema: Input parameter schema

    Returns:
        Decorated function
    """
    if SDK_AVAILABLE:
        return sdk_tool(name, description, input_schema)
    else:
        # Stub decorator that just returns the function
        def decorator(func: Callable) -> Callable:
            func._tool_name = name
            func._tool_description = description
            func._tool_input_schema = input_schema
            return func

        return decorator


async def safe_tool_execution(
    handler: ToolHandler,
    args: Dict[str, Any],
    timeout_seconds: int = 30,
) -> Dict[str, Any]:
    """Execute a tool handler with error handling and timeout.

    Args:
        handler: Tool handler function
        args: Arguments to pass to handler
        timeout_seconds: Timeout in seconds

    Returns:
        Tool result or error response
    """
    try:
        if asyncio.iscoroutinefunction(handler):
            result = await asyncio.wait_for(
                handler(args),
                timeout=timeout_seconds,
            )
        else:
            result = handler(args)

        return result

    except asyncio.TimeoutError:
        logger.error(
            "Tool execution timed out",
            timeout=timeout_seconds,
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Tool execution timed out after {timeout_seconds}s",
                }
            ],
            "isError": True,
        }

    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "Tool execution failed",
            error=str(e),
            error_type=error_type,
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Tool error ({error_type}): {str(e)}",
                }
            ],
            "isError": True,
        }


class ToolRegistry:
    """Registry for custom tools.

    Manages tool registration and provides MCP server configuration.
    """

    def __init__(self, timeout_seconds: int = 30) -> None:
        """Initialize the tool registry.

        Args:
            timeout_seconds: Default timeout for tool execution
        """
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.timeout_seconds = timeout_seconds

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        """Register a tool with the registry.

        Args:
            name: Tool name (should be prefixed with mcp server name)
            description: Human-readable description
            input_schema: JSON schema for input parameters
            handler: Async function to handle tool calls
        """

        # Wrap handler with safe execution
        async def safe_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            return await safe_tool_execution(
                handler,
                args,
                timeout_seconds=self.timeout_seconds,
            )

        self.tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "handler": safe_handler,
            "original_handler": handler,
        }

        logger.info("Registered tool", name=name, description=description)

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a registered tool by name.

        Args:
            name: Tool name

        Returns:
            Tool configuration or None if not found
        """
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def get_mcp_server_config(self) -> Dict[str, Any]:
        """Get MCP server configuration for registered tools.

        Returns:
            MCP server configuration dict
        """
        if SDK_AVAILABLE and self.tools:
            # Create actual MCP server with SDK
            tool_funcs = [
                tool_info["original_handler"] for tool_info in self.tools.values()
            ]

            try:
                server = create_sdk_mcp_server(
                    name="telegram",
                    version="1.0.0",
                    tools=tool_funcs,
                )
                return {"telegram": server}
            except Exception as e:
                logger.error("Failed to create MCP server", error=str(e))
                return {}
        else:
            # Return stub configuration
            return {
                "telegram": {
                    "name": "telegram",
                    "version": "1.0.0",
                    "tools": list(self.tools.keys()),
                }
            }

    async def execute_tool(
        self,
        name: str,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a registered tool by name.

        Args:
            name: Tool name
            args: Tool arguments

        Returns:
            Tool result
        """
        tool = self.get_tool(name)
        if not tool:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                "isError": True,
            }

        handler = tool["handler"]
        return await handler(args)


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry.

    Returns:
        Global ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
) -> Callable[[ToolHandler], ToolHandler]:
    """Decorator to register a tool with the global registry.

    Args:
        name: Tool name
        description: Tool description
        input_schema: Input schema

    Returns:
        Decorator function
    """

    def decorator(func: ToolHandler) -> ToolHandler:
        registry = get_registry()
        registry.register(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=func,
        )
        return func

    return decorator
