"""Claude Code integration module."""

# New modules - imported for registration
from . import commands, conversation, hooks, tools
from .agent_integration import AgentIntegration
from .conversation import (
    ConversationManager,
    get_conversation_manager,
    set_conversation_manager,
)
from .exceptions import (
    ClaudeError,
    ClaudeParsingError,
    ClaudeProcessError,
    ClaudeSessionError,
    ClaudeTimeoutError,
)
from .facade import ClaudeIntegration
from .integration import ClaudeProcessManager, ClaudeResponse, StreamUpdate
from .monitor import ToolMonitor
from .parser import OutputParser, ResponseFormatter
from .session import (
    ClaudeSession,
    InMemorySessionStorage,
    SessionManager,
    SessionStorage,
)

__all__ = [
    # Exceptions
    "ClaudeError",
    "ClaudeParsingError",
    "ClaudeProcessError",
    "ClaudeSessionError",
    "ClaudeTimeoutError",
    # Main integration
    "ClaudeIntegration",
    "AgentIntegration",
    # Core components
    "ClaudeProcessManager",
    "ClaudeResponse",
    "StreamUpdate",
    "SessionManager",
    "SessionStorage",
    "InMemorySessionStorage",
    "ClaudeSession",
    "ToolMonitor",
    "OutputParser",
    "ResponseFormatter",
    # Conversation management
    "ConversationManager",
    "get_conversation_manager",
    "set_conversation_manager",
    # New modules
    "tools",
    "hooks",
    "commands",
    "conversation",
]
