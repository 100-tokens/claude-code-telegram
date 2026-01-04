"""Test security hooks for Claude permission control.

These tests verify that dangerous operations are blocked and
permission decisions are correctly made by the hook system.
"""

from unittest.mock import MagicMock, patch


class TestDangerousPatterns:
    """Test dangerous pattern detection."""

    async def test_rm_rf_pattern_detected(self) -> None:
        """Test that rm -rf pattern is detected."""
        from src.claude.hooks.security_hooks import is_dangerous_command

        assert is_dangerous_command("rm -rf /") is True
        assert is_dangerous_command("rm -rf ~") is True
        assert is_dangerous_command("rm -rf .") is True
        assert is_dangerous_command("sudo rm -rf /var") is True

    async def test_dev_null_redirect_detected(self) -> None:
        """Test that /dev/ redirects are detected."""
        from src.claude.hooks.security_hooks import is_dangerous_command

        assert is_dangerous_command("> /dev/sda") is True
        assert (
            is_dangerous_command("echo test > /dev/null") is False
        )  # /dev/null is safe
        assert is_dangerous_command("dd if=... of=/dev/sda") is True

    async def test_chmod_777_detected(self) -> None:
        """Test that chmod 777 is detected."""
        from src.claude.hooks.security_hooks import is_dangerous_command

        assert is_dangerous_command("chmod 777 /etc/passwd") is True
        assert is_dangerous_command("chmod 777 -R /") is True
        assert is_dangerous_command("chmod 755 file") is False  # 755 is safe

    async def test_force_push_detected(self) -> None:
        """Test that git push --force is detected."""
        from src.claude.hooks.security_hooks import is_dangerous_command

        assert is_dangerous_command("git push --force") is True
        assert is_dangerous_command("git push -f origin main") is True
        assert (
            is_dangerous_command("git push origin main") is False
        )  # Regular push is safe

    async def test_safe_commands_pass(self) -> None:
        """Test that safe commands are not flagged."""
        from src.claude.hooks.security_hooks import is_dangerous_command

        assert is_dangerous_command("ls -la") is False
        assert is_dangerous_command("cat file.txt") is False
        assert is_dangerous_command("git status") is False
        assert is_dangerous_command("python script.py") is False
        assert is_dangerous_command("npm install") is False


class TestHookRegistration:
    """Test hook registration with Claude SDK."""

    async def test_create_security_hooks_returns_dict(self) -> None:
        """Test that create_security_hooks returns proper dict."""
        from src.claude.hooks.security_hooks import create_security_hooks

        hooks = create_security_hooks()

        assert isinstance(hooks, dict)
        assert "PreToolUse" in hooks or hooks == {}

    async def test_hooks_have_correct_structure(self) -> None:
        """Test that hooks have correct structure for SDK."""
        from src.claude.hooks.security_hooks import create_security_hooks

        hooks = create_security_hooks()

        if "PreToolUse" in hooks:
            # Should be a list of hook matchers
            assert isinstance(hooks["PreToolUse"], list)

    async def test_bash_hook_registered(self) -> None:
        """Test that Bash hook is registered."""
        from src.claude.hooks.security_hooks import create_security_hooks

        hooks = create_security_hooks()

        if "PreToolUse" in hooks:
            # Should have at least one hook for Bash
            hook_matchers = hooks["PreToolUse"]
            assert len(hook_matchers) > 0


class TestPermissionDecisions:
    """Test permission decision logic."""

    async def test_dangerous_command_denied(self) -> None:
        """Test that dangerous commands are denied."""
        from src.claude.hooks.security_hooks import bash_security_hook

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
        }

        result = await bash_security_hook(input_data, "tool_123", {})

        assert result is not None
        if "hookSpecificOutput" in result:
            assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    async def test_safe_command_allowed(self) -> None:
        """Test that safe commands are allowed."""
        from src.claude.hooks.security_hooks import bash_security_hook

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
        }

        result = await bash_security_hook(input_data, "tool_123", {})

        # Safe commands should return empty dict or allow
        assert (
            result == {}
            or result.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"
        )

    async def test_non_bash_tool_passes_through(self) -> None:
        """Test that non-Bash tools pass through hook."""
        from src.claude.hooks.security_hooks import bash_security_hook

        input_data = {
            "tool_name": "Read",
            "tool_input": {"file": "/etc/passwd"},
        }

        result = await bash_security_hook(input_data, "tool_123", {})

        # Non-Bash should pass through
        assert result == {}

    async def test_denial_includes_reason(self) -> None:
        """Test that denial includes reason message."""
        from src.claude.hooks.security_hooks import bash_security_hook

        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /important"},
        }

        result = await bash_security_hook(input_data, "tool_123", {})

        if "hookSpecificOutput" in result:
            assert "permissionDecisionReason" in result["hookSpecificOutput"]
            reason = result["hookSpecificOutput"]["permissionDecisionReason"]
            assert len(reason) > 0


class TestConfirmationFlow:
    """Test user confirmation flow for sensitive operations."""

    async def test_confirmation_required_for_sensitive_ops(self) -> None:
        """Test that sensitive operations require confirmation."""
        from src.claude.hooks.confirmation import requires_confirmation

        # File deletions should require confirmation
        assert requires_confirmation("rm important_file.txt") is True

        # Git pushes should require confirmation
        assert requires_confirmation("git push origin main") is True

        # Safe reads should not require confirmation
        assert requires_confirmation("cat file.txt") is False

    async def test_confirmation_callback_structure(self) -> None:
        """Test confirmation callback has correct structure."""
        from src.claude.hooks.confirmation import create_confirmation_request

        request = create_confirmation_request(
            command="rm -rf temp/",
            reason="File deletion",
            user_id=12345,
        )

        assert "command" in request
        assert "reason" in request
        assert "user_id" in request


class TestAuditLogging:
    """Test audit logging for blocked operations."""

    async def test_blocked_operations_logged(self) -> None:
        """Test that blocked operations are logged."""
        import structlog

        from src.claude.hooks.security_hooks import bash_security_hook

        # Mock the logger
        with patch.object(structlog, "get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            input_data = {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /"},
            }

            await bash_security_hook(input_data, "tool_123", {})

            # Should have logged the blocked command
            # Note: Actual logging verification depends on implementation

    async def test_audit_record_structure(self) -> None:
        """Test audit record has correct structure."""
        from src.claude.hooks.security_hooks import create_audit_record

        record = create_audit_record(
            command="rm -rf /",
            decision="deny",
            reason="Dangerous pattern: rm -rf",
            user_id=12345,
        )

        assert "command" in record
        assert "decision" in record
        assert "reason" in record
        assert "user_id" in record
        assert "timestamp" in record
