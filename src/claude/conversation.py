"""Bidirectional conversation management for Claude Agent SDK.

This module provides ConversationManager that bridges AgentIntegration
with SessionManager for stateful, interruptible conversations.
"""

import asyncio
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, Optional

import structlog

from .agent_integration import AgentIntegration, StreamUpdate
from .session import SessionManager

logger = structlog.get_logger(__name__)


class ConversationManager:
    """Manage bidirectional conversations with interrupt capability.

    This class bridges AgentIntegration (SDK communication) with
    SessionManager (session persistence) to provide:
    - Stateful conversations that persist across restarts
    - Per-user conversation tracking
    - Interrupt capability via stop_conversation()
    - Conversation context maintained across 50+ turns
    """

    def __init__(
        self,
        agent_integration: AgentIntegration,
        session_manager: SessionManager,
    ) -> None:
        """Initialize ConversationManager.

        Args:
            agent_integration: AgentIntegration instance for SDK communication
            session_manager: SessionManager instance for session persistence
        """
        self.agent = agent_integration
        self.session_manager = session_manager
        self._active_queries: Dict[int, bool] = {}  # user_id -> is_active
        self._cancel_flags: Dict[int, asyncio.Event] = {}  # user_id -> cancel_event
        self._lock = asyncio.Lock()

    async def start_conversation(
        self,
        user_id: int,
        project_path: Path,
        prompt: str,
        stream_callback: Optional[Callable[[StreamUpdate], Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Start or continue a conversation.

        Args:
            user_id: Telegram user ID
            project_path: Working directory for the conversation
            prompt: User's message
            stream_callback: Optional callback for streaming updates

        Yields:
            Response messages from Claude
        """
        # Get or create session
        session = await self.session_manager.get_or_create_session(
            user_id=user_id,
            project_path=project_path,
        )

        logger.info(
            "Starting conversation",
            user_id=user_id,
            session_id=session.session_id,
            project_path=str(project_path),
        )

        # Set up cancellation
        cancel_event = asyncio.Event()
        async with self._lock:
            self._active_queries[user_id] = True
            self._cancel_flags[user_id] = cancel_event

        try:
            # Query the agent
            async for response in self.agent.query(
                user_id=user_id,
                prompt=prompt,
                stream_callback=stream_callback,
            ):
                # Check for cancellation
                if cancel_event.is_set():
                    logger.info("Conversation cancelled", user_id=user_id)
                    yield {
                        "type": "cancelled",
                        "content": "Conversation was stopped by user.",
                    }
                    break

                yield response

        finally:
            # Cleanup
            async with self._lock:
                self._active_queries.pop(user_id, None)
                self._cancel_flags.pop(user_id, None)

    async def stop_conversation(self, user_id: int) -> bool:
        """Stop an active conversation.

        Args:
            user_id: Telegram user ID

        Returns:
            True if a conversation was stopped, False if no active conversation
        """
        async with self._lock:
            # Check if user has active query
            if not self._active_queries.get(user_id):
                logger.debug("No active conversation to stop", user_id=user_id)
                return False

            # Set cancel flag
            cancel_event = self._cancel_flags.get(user_id)
            if cancel_event:
                cancel_event.set()

            # Remove from active queries (cleanup)
            self._active_queries.pop(user_id, None)
            self._cancel_flags.pop(user_id, None)

        # Close the SDK session
        await self.agent.close_session(user_id)

        logger.info("Conversation stopped", user_id=user_id)
        return True

    def is_conversation_active(self, user_id: int) -> bool:
        """Check if a user has an active conversation.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user has an active query
        """
        return self._active_queries.get(user_id, False)

    async def get_conversation_info(
        self, user_id: int, project_path: Path
    ) -> Dict[str, Any]:
        """Get information about a user's conversation.

        Args:
            user_id: Telegram user ID
            project_path: Working directory

        Returns:
            Dict with conversation information
        """
        session = await self.session_manager.get_or_create_session(
            user_id=user_id,
            project_path=project_path,
        )

        return {
            "session_id": session.session_id,
            "project_path": str(session.project_path),
            "message_count": session.message_count,
            "total_cost": session.total_cost,
            "total_turns": session.total_turns,
            "is_active": self.is_conversation_active(user_id),
            "created_at": session.created_at.isoformat(),
            "last_used": session.last_used.isoformat(),
        }

    async def cleanup_inactive(self) -> int:
        """Cleanup inactive conversations and expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        return await self.session_manager.cleanup_expired_sessions()

    def get_active_count(self) -> int:
        """Get number of active conversations.

        Returns:
            Number of active conversations
        """
        return sum(1 for active in self._active_queries.values() if active)


# Module-level singleton
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> Optional[ConversationManager]:
    """Get the global ConversationManager instance.

    Returns:
        ConversationManager instance or None if not initialized
    """
    return _conversation_manager


def set_conversation_manager(manager: ConversationManager) -> None:
    """Set the global ConversationManager instance.

    Args:
        manager: ConversationManager instance
    """
    global _conversation_manager
    _conversation_manager = manager
