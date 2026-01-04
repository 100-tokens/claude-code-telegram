"""User confirmation flow for sensitive operations.

Provides utilities for requesting user confirmation before
executing potentially dangerous or irreversible commands.
"""

from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Commands that require user confirmation (but aren't blocked)
CONFIRMATION_PATTERNS: List[str] = [
    # File operations that could cause data loss
    "rm ",
    "rmdir ",
    "mv ",
    # Git operations that modify history or push
    "git push",
    "git rebase",
    "git merge",
    "git commit",
    "git stash drop",
    "git branch -d",
    "git branch -D",
    # Package management
    "pip uninstall",
    "npm uninstall",
    "poetry remove",
    # Database operations
    "drop ",
    "truncate ",
    "delete from",
]

# Commands that are safe and never need confirmation
SAFE_PATTERNS: List[str] = [
    "cat ",
    "head ",
    "tail ",
    "less ",
    "more ",
    "grep ",
    "find ",
    "ls ",
    "pwd",
    "echo ",
    "which ",
    "type ",
    "file ",
    "wc ",
    "sort ",
    "uniq ",
    "diff ",
    "git status",
    "git log",
    "git diff",
    "git show",
    "git branch",
    "git remote",
    "python --version",
    "node --version",
    "npm --version",
]


def requires_confirmation(command: str) -> bool:
    """Check if a command requires user confirmation.

    Args:
        command: Shell command to check

    Returns:
        True if the command should require confirmation
    """
    command_lower = command.lower().strip()

    # Check safe patterns first
    for safe in SAFE_PATTERNS:
        if command_lower.startswith(safe.lower()):
            return False

    # Check confirmation patterns
    for pattern in CONFIRMATION_PATTERNS:
        if pattern.lower() in command_lower:
            return True

    return False


def create_confirmation_request(
    command: str,
    reason: str,
    user_id: Optional[int] = None,
    additional_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a confirmation request for a sensitive operation.

    Args:
        command: The command requiring confirmation
        reason: Why confirmation is needed
        user_id: Optional user ID
        additional_context: Optional additional context

    Returns:
        Confirmation request dict
    """
    request: Dict[str, Any] = {
        "command": command,
        "reason": reason,
        "type": "command_confirmation",
    }

    if user_id is not None:
        request["user_id"] = user_id

    if additional_context:
        request["context"] = additional_context

    return request


def format_confirmation_message(
    command: str,
    reason: str,
    preview: Optional[str] = None,
) -> str:
    """Format a user-friendly confirmation message.

    Args:
        command: The command to confirm
        reason: Why confirmation is needed
        preview: Optional preview of what the command will do

    Returns:
        Formatted confirmation message
    """
    lines = [
        "**Confirmation Required**",
        "",
        f"Command: `{command[:100]}`" + ("..." if len(command) > 100 else ""),
        f"Reason: {reason}",
    ]

    if preview:
        lines.extend(
            [
                "",
                "Preview:",
                f"```{preview}```",
            ]
        )

    lines.extend(
        [
            "",
            "Reply with **yes** to proceed or **no** to cancel.",
        ]
    )

    return "\n".join(lines)


class ConfirmationState:
    """Track pending confirmations for users.

    Stores pending confirmation requests keyed by user ID,
    allowing async confirmation flows.
    """

    def __init__(self) -> None:
        """Initialize confirmation state."""
        self._pending: Dict[int, Dict[str, Any]] = {}

    def set_pending(
        self,
        user_id: int,
        command: str,
        reason: str,
        callback_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set a pending confirmation for a user.

        Args:
            user_id: User ID
            command: Command awaiting confirmation
            reason: Reason for confirmation
            callback_data: Optional data to include when confirmed
        """
        self._pending[user_id] = {
            "command": command,
            "reason": reason,
            "callback_data": callback_data or {},
        }

        logger.debug(
            "Set pending confirmation",
            user_id=user_id,
            command=command[:50],
        )

    def get_pending(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get pending confirmation for a user.

        Args:
            user_id: User ID

        Returns:
            Pending confirmation dict or None
        """
        return self._pending.get(user_id)

    def clear_pending(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Clear and return pending confirmation for a user.

        Args:
            user_id: User ID

        Returns:
            The cleared pending confirmation or None
        """
        return self._pending.pop(user_id, None)

    def has_pending(self, user_id: int) -> bool:
        """Check if user has pending confirmation.

        Args:
            user_id: User ID

        Returns:
            True if user has pending confirmation
        """
        return user_id in self._pending


# Global confirmation state instance
_confirmation_state: Optional[ConfirmationState] = None


def get_confirmation_state() -> ConfirmationState:
    """Get the global confirmation state instance.

    Returns:
        ConfirmationState instance
    """
    global _confirmation_state
    if _confirmation_state is None:
        _confirmation_state = ConfirmationState()
    return _confirmation_state
