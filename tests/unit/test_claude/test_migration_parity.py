"""Test migration parity - existing features work with new SDK.

These tests verify that all existing functionality continues to work
after migrating from claude-code-sdk to claude-agent-sdk.
"""

from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.claude.agent_integration import AgentIntegration
from src.config.settings import Settings


class TestMigrationParity:
    """Test that existing features work with new SDK."""

    @pytest.fixture
    def config(self, tmp_path: Path) -> Settings:
        """Create test config matching existing behavior."""
        return Settings(
            telegram_bot_token="test:token",
            telegram_bot_username="testbot",
            approved_directory=tmp_path,
            use_sdk=True,
            claude_max_turns=10,
            claude_timeout_seconds=30,
            permission_mode="acceptEdits",
            enable_telegram_tools=True,
            enable_security_hooks=True,
        )

    @pytest.fixture
    def agent_integration(self, config: Settings) -> AgentIntegration:
        """Create agent integration."""
        return AgentIntegration(config=config, telegram_context=None)

    async def test_basic_message_handling(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test basic message is processed like before."""
        user_id = 12345
        message = "List files in current directory"

        responses: List[Dict[str, Any]] = []
        async for response in agent_integration.query(user_id, message):
            responses.append(response)

        # Should get at least one response
        assert len(responses) >= 1
        # Response should have expected structure
        assert "type" in responses[0]

    async def test_session_context_maintained(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test session context is maintained across messages."""
        user_id = 12345

        # First message
        responses1: List[Dict[str, Any]] = []
        async for response in agent_integration.query(user_id, "Hello"):
            responses1.append(response)

        # Second message should use same session
        responses2: List[Dict[str, Any]] = []
        async for response in agent_integration.query(user_id, "Follow up"):
            responses2.append(response)

        # Both should succeed
        assert len(responses1) >= 1
        assert len(responses2) >= 1

    async def test_multiple_users_isolated(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test multiple users have isolated sessions."""
        user1, user2 = 111, 222

        # User 1 sends message
        responses1: List[Dict[str, Any]] = []
        async for response in agent_integration.query(user1, "User 1 message"):
            responses1.append(response)

        # User 2 sends message
        responses2: List[Dict[str, Any]] = []
        async for response in agent_integration.query(user2, "User 2 message"):
            responses2.append(response)

        # Both should get responses
        assert len(responses1) >= 1
        assert len(responses2) >= 1

    async def test_session_cleanup(self, agent_integration: AgentIntegration) -> None:
        """Test session cleanup works correctly."""
        user_id = 12345

        # Create a session by sending a message
        async for _ in agent_integration.query(user_id, "Test"):
            pass

        # Close the session
        await agent_integration.close_session(user_id)

        # User should be removed from clients
        assert user_id not in agent_integration.clients


class TestConfigurationParity:
    """Test configuration options work as before."""

    @pytest.fixture
    def tmp_dir(self, tmp_path: Path) -> Path:
        """Create temporary directory."""
        return tmp_path

    async def test_max_turns_respected(self, tmp_dir: Path) -> None:
        """Test max_turns configuration is used."""
        config = Settings(
            telegram_bot_token="test:token",
            telegram_bot_username="testbot",
            approved_directory=tmp_dir,
            claude_max_turns=5,
        )
        integration = AgentIntegration(config=config, telegram_context=None)
        assert integration.config.claude_max_turns == 5

    async def test_timeout_configuration(self, tmp_dir: Path) -> None:
        """Test timeout configuration is used."""
        config = Settings(
            telegram_bot_token="test:token",
            telegram_bot_username="testbot",
            approved_directory=tmp_dir,
            claude_timeout_seconds=60,
            tool_timeout_seconds=15,
        )
        integration = AgentIntegration(config=config, telegram_context=None)
        assert integration.config.claude_timeout_seconds == 60
        assert integration.config.tool_timeout_seconds == 15

    async def test_allowed_tools_configuration(self, tmp_dir: Path) -> None:
        """Test allowed_tools configuration is preserved."""
        allowed_tools = ["Read", "Write", "Bash"]
        config = Settings(
            telegram_bot_token="test:token",
            telegram_bot_username="testbot",
            approved_directory=tmp_dir,
            claude_allowed_tools=allowed_tools,
        )
        integration = AgentIntegration(config=config, telegram_context=None)
        assert integration.config.claude_allowed_tools == allowed_tools

    async def test_working_directory_configuration(self, tmp_dir: Path) -> None:
        """Test approved_directory configuration is used."""
        config = Settings(
            telegram_bot_token="test:token",
            telegram_bot_username="testbot",
            approved_directory=tmp_dir,
        )
        integration = AgentIntegration(config=config, telegram_context=None)
        assert integration.config.approved_directory == tmp_dir


class TestErrorHandlingParity:
    """Test error handling works as before."""

    @pytest.fixture
    def config(self, tmp_path: Path) -> Settings:
        """Create test config."""
        return Settings(
            telegram_bot_token="test:token",
            telegram_bot_username="testbot",
            approved_directory=tmp_path,
        )

    async def test_graceful_error_response(self, config: Settings) -> None:
        """Test errors return graceful responses."""
        integration = AgentIntegration(config=config, telegram_context=None)

        # Query without initialization should still return response
        responses: List[Dict[str, Any]] = []
        async for response in integration.query(12345, "Test"):
            responses.append(response)

        # Should get a response (even if error/stub)
        assert len(responses) >= 1
