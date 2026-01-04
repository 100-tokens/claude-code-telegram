"""Permission control hooks for Claude Agent SDK.

This module provides PreToolUse hooks that intercept and control
Claude's tool usage for security enforcement.
"""

from .confirmation import (
    ConfirmationState,
    create_confirmation_request,
    format_confirmation_message,
    get_confirmation_state,
    requires_confirmation,
)
from .security_hooks import (
    DANGEROUS_PATTERNS,
    bash_security_hook,
    create_audit_record,
    create_security_hooks,
    get_dangerous_pattern_match,
    is_dangerous_command,
    log_security_event,
)

__all__ = [
    # Security hooks
    "DANGEROUS_PATTERNS",
    "bash_security_hook",
    "create_audit_record",
    "create_security_hooks",
    "get_dangerous_pattern_match",
    "is_dangerous_command",
    "log_security_event",
    # Confirmation flow
    "ConfirmationState",
    "create_confirmation_request",
    "format_confirmation_message",
    "get_confirmation_state",
    "requires_confirmation",
]
