"""Security hooks for Claude Agent SDK permission control.

Provides PreToolUse hooks that intercept dangerous operations
and enforce security policies before tool execution.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Dangerous command patterns that should be blocked or require confirmation
# Each pattern is a tuple of (regex_pattern, description, action)
# action: 'deny' = always block, 'confirm' = require user confirmation
DANGEROUS_PATTERNS: List[tuple[str, str, str]] = [
    # Destructive file operations
    (r"rm\s+(-[rf]+\s+)*[/~.]", "Recursive/forced file deletion", "deny"),
    (r"rm\s+-[a-z]*r[a-z]*\s+-[a-z]*f", "Recursive forced deletion", "deny"),
    (r"rm\s+-[a-z]*f[a-z]*\s+-[a-z]*r", "Forced recursive deletion", "deny"),
    # Device writes (except /dev/null)
    (r">\s*/dev/(?!null)", "Write to device file", "deny"),
    (r"dd\s+.*of=/dev/(?!null)", "Direct device write with dd", "deny"),
    # Dangerous permissions
    (r"chmod\s+777", "World-writable permissions", "deny"),
    (r"chmod\s+-R\s+777", "Recursive world-writable permissions", "deny"),
    # Git destructive operations
    (r"git\s+push\s+.*--force", "Force push to remote", "deny"),
    (r"git\s+push\s+.*-f\b", "Force push to remote", "deny"),
    (r"git\s+reset\s+--hard", "Hard reset (destructive)", "confirm"),
    (r"git\s+clean\s+-[a-z]*f", "Force clean untracked files", "confirm"),
    # System modification
    (r"mkfs\.", "Filesystem creation", "deny"),
    (r"fdisk\s+", "Disk partitioning", "deny"),
    (r"format\s+", "Disk formatting", "deny"),
    # Network exfiltration patterns
    (r"curl\s+.*\|\s*bash", "Piped curl to bash", "deny"),
    (r"wget\s+.*\|\s*bash", "Piped wget to bash", "deny"),
    (r"curl\s+.*\|\s*sh", "Piped curl to shell", "deny"),
    (r"wget\s+.*\|\s*sh", "Piped wget to shell", "deny"),
    # Fork bombs and resource exhaustion
    (r":\(\)\s*\{\s*:\|:&\s*\};\s*:", "Fork bomb", "deny"),
    (r"while\s+true.*do.*done", "Infinite loop", "confirm"),
]

# Compiled patterns for efficiency
_COMPILED_PATTERNS: Optional[List[tuple[re.Pattern, str, str]]] = None


def _get_compiled_patterns() -> List[tuple[re.Pattern, str, str]]:
    """Get compiled regex patterns (lazy initialization)."""
    global _COMPILED_PATTERNS
    if _COMPILED_PATTERNS is None:
        _COMPILED_PATTERNS = [
            (re.compile(pattern, re.IGNORECASE), desc, action)
            for pattern, desc, action in DANGEROUS_PATTERNS
        ]
    return _COMPILED_PATTERNS


def is_dangerous_command(command: str) -> bool:
    """Check if a command matches any dangerous pattern.

    Args:
        command: The shell command to check

    Returns:
        True if the command matches a dangerous pattern
    """
    patterns = _get_compiled_patterns()
    for pattern, _, action in patterns:
        if action == "deny" and pattern.search(command):
            return True
    return False


def get_dangerous_pattern_match(command: str) -> Optional[Dict[str, str]]:
    """Get details about why a command is dangerous.

    Args:
        command: The shell command to check

    Returns:
        Dict with 'pattern', 'description', 'action' or None
    """
    patterns = _get_compiled_patterns()
    for pattern, description, action in patterns:
        if pattern.search(command):
            return {
                "pattern": pattern.pattern,
                "description": description,
                "action": action,
            }
    return None


async def bash_security_hook(
    input_data: Dict[str, Any],
    tool_use_id: str,
    session_state: Dict[str, Any],
) -> Dict[str, Any]:
    """PreToolUse hook for Bash tool security.

    Intercepts Bash tool calls and checks for dangerous patterns.
    Returns permission decision for the SDK.

    Args:
        input_data: Tool input containing tool_name and tool_input
        tool_use_id: Unique ID for this tool use
        session_state: Session state dict (unused currently)

    Returns:
        Hook result dict with permission decision
    """
    # Only process Bash tool
    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        return {}

    # Extract command from tool input
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        return {}

    # Check for dangerous patterns
    match = get_dangerous_pattern_match(command)

    if match is None:
        # Command is safe, allow execution
        return {}

    # Log the blocked/flagged command
    logger.warning(
        "Dangerous command detected",
        command=command[:100],  # Truncate for logging
        pattern=match["description"],
        action=match["action"],
        tool_use_id=tool_use_id,
    )

    if match["action"] == "deny":
        # Block the command
        return {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Command blocked: {match['description']}. "
                    f"This operation is not allowed for security reasons."
                ),
            }
        }

    elif match["action"] == "confirm":
        # Request user confirmation
        return {
            "hookSpecificOutput": {
                "permissionDecision": "askUser",
                "permissionDecisionReason": (
                    f"This command requires confirmation: {match['description']}. "
                    f"Command: {command[:50]}..."
                ),
            }
        }

    return {}


def create_security_hooks() -> Dict[str, List[Dict[str, Any]]]:
    """Create security hooks configuration for Claude Agent SDK.

    Returns a hooks dict compatible with ClaudeAgentOptions.hooks.

    Returns:
        Dict with PreToolUse hooks list
    """
    return {
        "PreToolUse": [
            {
                "matcher": {"tool_name": "Bash"},
                "callback": bash_security_hook,
            }
        ]
    }


def create_audit_record(
    command: str,
    decision: str,
    reason: str,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create an audit record for a security decision.

    Args:
        command: The command that was evaluated
        decision: The permission decision (allow, deny, confirm)
        reason: Reason for the decision
        user_id: Optional user ID for attribution

    Returns:
        Audit record dict
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "decision": decision,
        "reason": reason,
        "user_id": user_id,
    }


def log_security_event(
    event_type: str,
    command: str,
    decision: str,
    reason: str,
    user_id: Optional[int] = None,
) -> None:
    """Log a security event for audit purposes.

    Args:
        event_type: Type of event (blocked, confirmed, allowed)
        command: The command that was evaluated
        decision: The permission decision
        reason: Reason for the decision
        user_id: Optional user ID
    """
    record = create_audit_record(command, decision, reason, user_id)

    logger.info(
        "Security event",
        event_type=event_type,
        **record,
    )
