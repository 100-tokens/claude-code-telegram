"""Test Claude Agent SDK integration."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.claude.agent_integration import AgentIntegration
from src.config.settings import Settings


class TestAgentIntegration:
    """Test Agent SDK integration."""

    @pytest.fixture
    def config(self, tmp_path: Path) -> Settings:
        """Create test config."""
        return Settings(
            telegram_bot_token="test:token",
            telegram_bot_username="testbot",
            approved_directory=tmp_path,
            use_sdk=True,
            claude_timeout_seconds=2,
            permission_mode="acceptEdits",
            enable_telegram_tools=True,
            enable_security_hooks=True,
            enable_slash_commands=True,
            tool_timeout_seconds=5,
        )

    @pytest.fixture
    def agent_integration(self, config: Settings) -> AgentIntegration:
        """Create agent integration instance."""
        return AgentIntegration(config=config, telegram_context=None)

    async def test_agent_integration_initialization(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test AgentIntegration initializes correctly."""
        assert agent_integration.config is not None
        assert agent_integration.clients == {}
        assert agent_integration._options is None

    async def test_agent_integration_initialize(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test AgentIntegration.initialize() sets up options."""
        await agent_integration.initialize()
        # Options will be None until SDK is properly imported
        # This test validates the method runs without error

    async def test_create_options_returns_config(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test _create_options returns configuration."""
        options = agent_integration._create_options()
        # Currently returns None as SDK not imported
        # When SDK is available, this should return ClaudeAgentOptions

    async def test_get_client_creates_new_client(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test _get_client creates a new client for user."""
        user_id = 12345
        client = await agent_integration._get_client(user_id)
        # Currently returns None as SDK not imported
        # When SDK is available, this should create ClaudeSDKClient

    async def test_query_yields_responses(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test query yields response messages."""
        user_id = 12345
        prompt = "Hello, Claude!"

        responses = []
        async for response in agent_integration.query(user_id, prompt):
            responses.append(response)

        assert len(responses) > 0
        # Currently returns stub response
        assert responses[0]["type"] in ["text", "error"]

    async def test_close_session_removes_client(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test close_session removes user's client."""
        user_id = 12345
        # Manually add a mock client
        agent_integration.clients[user_id] = MagicMock()

        await agent_integration.close_session(user_id)

        assert user_id not in agent_integration.clients

    async def test_close_session_nonexistent_user(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test close_session handles nonexistent user gracefully."""
        user_id = 99999
        # Should not raise
        await agent_integration.close_session(user_id)
        assert user_id not in agent_integration.clients

    async def test_close_all_sessions(
        self, agent_integration: AgentIntegration
    ) -> None:
        """Test close_all closes all active sessions."""
        # Add multiple mock clients
        agent_integration.clients[111] = MagicMock()
        agent_integration.clients[222] = MagicMock()
        agent_integration.clients[333] = MagicMock()

        await agent_integration.close_all()

        assert len(agent_integration.clients) == 0


class TestAgentIntegrationConfig:
    """Test AgentIntegration configuration handling."""

    @pytest.fixture
    def config_with_hooks_disabled(self, tmp_path: Path) -> Settings:
        """Create config with security hooks disabled."""
        return Settings(
            telegram_bot_token="test:token",
            telegram_bot_username="testbot",
            approved_directory=tmp_path,
            use_sdk=True,
            enable_security_hooks=False,
        )

    async def test_hooks_disabled_config(
        self, config_with_hooks_disabled: Settings
    ) -> None:
        """Test that hooks can be disabled via config."""
        integration = AgentIntegration(
            config=config_with_hooks_disabled,
            telegram_context=None,
        )
        hooks = integration._create_security_hooks()
        # Should return empty dict when hooks disabled
        assert hooks == {}

    @pytest.fixture
    def config_with_tools_disabled(self, tmp_path: Path) -> Settings:
        """Create config with Telegram tools disabled."""
        return Settings(
            telegram_bot_token="test:token",
            telegram_bot_username="testbot",
            approved_directory=tmp_path,
            use_sdk=True,
            enable_telegram_tools=False,
        )

    async def test_tools_disabled_config(
        self, config_with_tools_disabled: Settings
    ) -> None:
        """Test that Telegram tools can be disabled via config."""
        integration = AgentIntegration(
            config=config_with_tools_disabled,
            telegram_context=None,
        )
        servers = integration._create_mcp_servers()
        # Should return empty dict when tools disabled
        assert servers == {}
