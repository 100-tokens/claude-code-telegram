"""Test session management and bidirectional conversation support.

These tests verify session lifecycle, interrupt handling, and
integration with the Claude Agent SDK.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock


class TestSessionLifecycle:
    """Test session creation, persistence, and cleanup."""

    async def test_session_creation(self) -> None:
        """Test that sessions are created correctly."""
        from src.claude.session import (
            ClaudeSession,
            InMemorySessionStorage,
            SessionManager,
        )
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.session_timeout_hours = 24
        config.max_sessions_per_user = 5

        storage = InMemorySessionStorage()
        manager = SessionManager(config, storage)

        session = await manager.get_or_create_session(
            user_id=12345,
            project_path=Path("/test/project"),
        )

        assert session is not None
        assert session.user_id == 12345
        assert session.project_path == Path("/test/project")
        assert session.session_id is not None

    async def test_session_reuse(self) -> None:
        """Test that existing sessions are reused."""
        from src.claude.session import (
            ClaudeSession,
            InMemorySessionStorage,
            SessionManager,
        )
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.session_timeout_hours = 24
        config.max_sessions_per_user = 5

        storage = InMemorySessionStorage()
        manager = SessionManager(config, storage)

        # Create first session
        session1 = await manager.get_or_create_session(
            user_id=12345,
            project_path=Path("/test/project"),
        )

        # Get same session by ID
        session2 = await manager.get_or_create_session(
            user_id=12345,
            project_path=Path("/test/project"),
            session_id=session1.session_id,
        )

        assert session1.session_id == session2.session_id

    async def test_session_expiration(self) -> None:
        """Test that expired sessions are handled correctly."""
        from src.claude.session import ClaudeSession

        session = ClaudeSession(
            session_id="test-123",
            user_id=12345,
            project_path=Path("/test"),
            created_at=datetime.utcnow() - timedelta(hours=25),
            last_used=datetime.utcnow() - timedelta(hours=25),
        )

        # Session should be expired with 24 hour timeout
        assert session.is_expired(24) is True

        # Session should not be expired with 48 hour timeout
        assert session.is_expired(48) is False

    async def test_session_cleanup(self) -> None:
        """Test that expired sessions are cleaned up."""
        from src.claude.session import (
            ClaudeSession,
            InMemorySessionStorage,
            SessionManager,
        )
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.session_timeout_hours = 1
        config.max_sessions_per_user = 5

        storage = InMemorySessionStorage()
        manager = SessionManager(config, storage)

        # Create session
        session = await manager.get_or_create_session(
            user_id=12345,
            project_path=Path("/test/project"),
        )

        # Manually expire the session
        session.last_used = datetime.utcnow() - timedelta(hours=2)
        await storage.save_session(session)

        # Cleanup should remove expired session
        removed_count = await manager.cleanup_expired_sessions()
        assert removed_count == 1

    async def test_max_sessions_per_user(self) -> None:
        """Test that max sessions per user is enforced."""
        from src.claude.session import InMemorySessionStorage, SessionManager
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.session_timeout_hours = 24
        config.max_sessions_per_user = 2

        storage = InMemorySessionStorage()
        manager = SessionManager(config, storage)

        # Create max sessions
        session1 = await manager.get_or_create_session(
            user_id=12345,
            project_path=Path("/test/project1"),
        )
        session2 = await manager.get_or_create_session(
            user_id=12345,
            project_path=Path("/test/project2"),
        )

        # Creating third session should remove oldest
        session3 = await manager.get_or_create_session(
            user_id=12345,
            project_path=Path("/test/project3"),
        )

        user_sessions = await manager._get_user_sessions(12345)
        assert len(user_sessions) <= 2


class TestInterruptHandling:
    """Test session interrupt and stop functionality."""

    async def test_close_session(self) -> None:
        """Test that sessions can be closed."""
        from src.claude.agent_integration import AgentIntegration
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.anthropic_api_key_str = None
        config.enable_telegram_tools = False
        config.enable_security_hooks = False
        config.claude_max_turns = 10
        config.claude_allowed_tools = []
        config.permission_mode = "acceptEdits"
        config.approved_directory = Path("/test")
        config.claude_timeout_seconds = 30
        config.tool_timeout_seconds = 10

        agent = AgentIntegration(config=config)
        await agent.initialize()

        # Simulate active client
        agent.clients[12345] = {"session_id": "test-123"}

        # Close session
        await agent.close_session(12345)

        # Client should be removed
        assert 12345 not in agent.clients

    async def test_close_all_sessions(self) -> None:
        """Test that all sessions can be closed."""
        from src.claude.agent_integration import AgentIntegration
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.anthropic_api_key_str = None
        config.enable_telegram_tools = False
        config.enable_security_hooks = False
        config.claude_max_turns = 10
        config.claude_allowed_tools = []
        config.permission_mode = "acceptEdits"
        config.approved_directory = Path("/test")
        config.claude_timeout_seconds = 30
        config.tool_timeout_seconds = 10

        agent = AgentIntegration(config=config)
        await agent.initialize()

        # Simulate multiple active clients
        agent.clients[12345] = {"session_id": "test-123"}
        agent.clients[67890] = {"session_id": "test-456"}

        # Close all sessions
        await agent.close_all()

        # All clients should be removed
        assert len(agent.clients) == 0

    async def test_session_count(self) -> None:
        """Test that active session count is tracked."""
        from src.claude.agent_integration import AgentIntegration
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.anthropic_api_key_str = None
        config.enable_telegram_tools = False
        config.enable_security_hooks = False
        config.claude_max_turns = 10
        config.claude_allowed_tools = []
        config.permission_mode = "acceptEdits"
        config.approved_directory = Path("/test")
        config.claude_timeout_seconds = 30
        config.tool_timeout_seconds = 10

        agent = AgentIntegration(config=config)

        assert agent.get_active_session_count() == 0

        agent.clients[12345] = {"session_id": "test-123"}
        assert agent.get_active_session_count() == 1

        agent.clients[67890] = {"session_id": "test-456"}
        assert agent.get_active_session_count() == 2


class TestConversationManager:
    """Test ConversationManager bridging AgentIntegration and SessionManager."""

    async def test_conversation_manager_creation(self) -> None:
        """Test ConversationManager is created correctly."""
        from src.claude.agent_integration import AgentIntegration
        from src.claude.conversation import ConversationManager
        from src.claude.session import InMemorySessionStorage, SessionManager
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.anthropic_api_key_str = None
        config.enable_telegram_tools = False
        config.enable_security_hooks = False
        config.claude_max_turns = 10
        config.claude_allowed_tools = []
        config.permission_mode = "acceptEdits"
        config.approved_directory = Path("/test")
        config.claude_timeout_seconds = 30
        config.tool_timeout_seconds = 10
        config.session_timeout_hours = 24
        config.max_sessions_per_user = 5

        storage = InMemorySessionStorage()
        session_manager = SessionManager(config, storage)
        agent = AgentIntegration(config=config)

        conversation_manager = ConversationManager(
            agent_integration=agent,
            session_manager=session_manager,
        )

        assert conversation_manager is not None

    async def test_stop_conversation(self) -> None:
        """Test that conversations can be stopped."""
        from src.claude.agent_integration import AgentIntegration
        from src.claude.conversation import ConversationManager
        from src.claude.session import InMemorySessionStorage, SessionManager
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.anthropic_api_key_str = None
        config.enable_telegram_tools = False
        config.enable_security_hooks = False
        config.claude_max_turns = 10
        config.claude_allowed_tools = []
        config.permission_mode = "acceptEdits"
        config.approved_directory = Path("/test")
        config.claude_timeout_seconds = 30
        config.tool_timeout_seconds = 10
        config.session_timeout_hours = 24
        config.max_sessions_per_user = 5

        storage = InMemorySessionStorage()
        session_manager = SessionManager(config, storage)
        agent = AgentIntegration(config=config)
        await agent.initialize()

        # Simulate active conversation
        agent.clients[12345] = {"session_id": "test-123"}

        conversation_manager = ConversationManager(
            agent_integration=agent,
            session_manager=session_manager,
        )

        # Mark conversation as in progress
        conversation_manager._active_queries[12345] = True

        # Stop should clear the flag and close session
        result = await conversation_manager.stop_conversation(12345)

        assert result is True
        assert 12345 not in conversation_manager._active_queries

    async def test_is_conversation_active(self) -> None:
        """Test checking if a conversation is active."""
        from src.claude.agent_integration import AgentIntegration
        from src.claude.conversation import ConversationManager
        from src.claude.session import InMemorySessionStorage, SessionManager
        from src.config.settings import Settings

        config = MagicMock(spec=Settings)
        config.anthropic_api_key_str = None
        config.enable_telegram_tools = False
        config.enable_security_hooks = False
        config.claude_max_turns = 10
        config.claude_allowed_tools = []
        config.permission_mode = "acceptEdits"
        config.approved_directory = Path("/test")
        config.claude_timeout_seconds = 30
        config.tool_timeout_seconds = 10
        config.session_timeout_hours = 24
        config.max_sessions_per_user = 5

        storage = InMemorySessionStorage()
        session_manager = SessionManager(config, storage)
        agent = AgentIntegration(config=config)

        conversation_manager = ConversationManager(
            agent_integration=agent,
            session_manager=session_manager,
        )

        # Initially not active
        assert conversation_manager.is_conversation_active(12345) is False

        # Mark as active
        conversation_manager._active_queries[12345] = True
        assert conversation_manager.is_conversation_active(12345) is True


class TestSessionStorage:
    """Test session storage integration."""

    async def test_in_memory_storage(self) -> None:
        """Test in-memory session storage."""
        from src.claude.session import ClaudeSession, InMemorySessionStorage

        storage = InMemorySessionStorage()

        session = ClaudeSession(
            session_id="test-123",
            user_id=12345,
            project_path=Path("/test"),
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
        )

        await storage.save_session(session)
        loaded = await storage.load_session("test-123")

        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.user_id == session.user_id

    async def test_delete_session(self) -> None:
        """Test session deletion."""
        from src.claude.session import ClaudeSession, InMemorySessionStorage

        storage = InMemorySessionStorage()

        session = ClaudeSession(
            session_id="test-123",
            user_id=12345,
            project_path=Path("/test"),
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
        )

        await storage.save_session(session)
        await storage.delete_session("test-123")

        loaded = await storage.load_session("test-123")
        assert loaded is None

    async def test_get_user_sessions(self) -> None:
        """Test getting all sessions for a user."""
        from src.claude.session import ClaudeSession, InMemorySessionStorage

        storage = InMemorySessionStorage()

        # Create sessions for different users
        session1 = ClaudeSession(
            session_id="test-1",
            user_id=12345,
            project_path=Path("/test1"),
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
        )
        session2 = ClaudeSession(
            session_id="test-2",
            user_id=12345,
            project_path=Path("/test2"),
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
        )
        session3 = ClaudeSession(
            session_id="test-3",
            user_id=67890,
            project_path=Path("/test3"),
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
        )

        await storage.save_session(session1)
        await storage.save_session(session2)
        await storage.save_session(session3)

        user_sessions = await storage.get_user_sessions(12345)
        assert len(user_sessions) == 2
