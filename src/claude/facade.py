"""High-level Claude Code integration facade.

Provides simple interface for bot handlers.
Supports both legacy SDK and new Agent SDK integration.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import structlog

from ..config.settings import Settings
from .agent_integration import AgentIntegration
from .agent_integration import StreamUpdate as AgentStreamUpdate
from .commands.executor import CommandExecutor, is_slash_command
from .exceptions import ClaudeToolValidationError
from .integration import ClaudeProcessManager, ClaudeResponse, StreamUpdate
from .monitor import ToolMonitor
from .sdk_integration import ClaudeSDKManager
from .session import SessionManager

logger = structlog.get_logger()


class ClaudeIntegration:
    """Main integration point for Claude Code.

    Supports three execution modes:
    1. AgentIntegration (new claude-agent-sdk) - preferred
    2. ClaudeSDKManager (legacy claude-code-sdk) - fallback
    3. ClaudeProcessManager (subprocess) - final fallback
    """

    def __init__(
        self,
        config: Settings,
        process_manager: Optional[ClaudeProcessManager] = None,
        sdk_manager: Optional[ClaudeSDKManager] = None,
        agent_integration: Optional[AgentIntegration] = None,
        session_manager: Optional[SessionManager] = None,
        tool_monitor: Optional[ToolMonitor] = None,
        telegram_context: Optional[Any] = None,
    ):
        """Initialize Claude integration facade.

        Args:
            config: Application settings
            process_manager: Optional subprocess manager (legacy)
            sdk_manager: Optional SDK manager (legacy claude-code-sdk)
            agent_integration: Optional Agent integration (new claude-agent-sdk)
            session_manager: Session management
            tool_monitor: Tool monitoring and validation
            telegram_context: Telegram context for custom tools
        """
        self.config = config
        self.telegram_context = telegram_context

        # Initialize new Agent SDK integration (preferred)
        self.agent_integration = agent_integration or AgentIntegration(
            config=config,
            telegram_context=telegram_context,
        )

        # Initialize legacy managers for fallback capability
        self.sdk_manager = (
            sdk_manager or ClaudeSDKManager(config) if config.use_sdk else None
        )
        self.process_manager = process_manager or ClaudeProcessManager(config)

        # Use Agent SDK by default if available, else legacy SDK, else subprocess
        if self.agent_integration.is_sdk_available:
            self.manager = self.agent_integration
            logger.info(
                "Using Agent SDK integration",
                sdk_type=self.agent_integration.sdk_type,
            )
        elif config.use_sdk and self.sdk_manager:
            self.manager = self.sdk_manager
            logger.info("Using legacy SDK manager")
        else:
            self.manager = self.process_manager
            logger.info("Using subprocess manager")

        self.session_manager = session_manager
        self.tool_monitor = tool_monitor
        self._sdk_failed_count = 0  # Track SDK failures for adaptive fallback

        # Initialize command executor for slash commands
        self.command_executor = (
            CommandExecutor(config.approved_directory / ".claude" / "commands")
            if config.enable_slash_commands
            else None
        )

    async def run_command(
        self,
        prompt: str,
        working_directory: Path,
        user_id: int,
        session_id: Optional[str] = None,
        on_stream: Optional[Callable[[StreamUpdate], None]] = None,
    ) -> ClaudeResponse:
        """Run Claude Code command with full integration."""
        # Process slash commands if enabled
        if self.command_executor and is_slash_command(prompt):
            logger.info(
                "Processing slash command",
                user_id=user_id,
                prompt_preview=prompt[:50],
            )

            result = await self.command_executor.process_message(prompt, user_id)

            if result["error"]:
                # Return error as ClaudeResponse
                return ClaudeResponse(
                    content=result["error"],
                    session_id=session_id or "",
                    cost=0.0,
                    duration_ms=0,
                    num_turns=0,
                    is_error=True,
                    error_type="command_error",
                )

            # Use expanded prompt
            prompt = result["expanded_prompt"]
            logger.info(
                "Expanded slash command",
                command=result["command"],
                expanded_length=len(prompt),
            )

        logger.info(
            "Running Claude command",
            user_id=user_id,
            working_directory=str(working_directory),
            session_id=session_id,
            prompt_length=len(prompt),
        )

        # Get or create session
        session = await self.session_manager.get_or_create_session(
            user_id, working_directory, session_id
        )

        # Track streaming updates and validate tool calls
        tools_validated = True
        validation_errors = []
        blocked_tools = set()

        async def stream_handler(update: StreamUpdate):
            nonlocal tools_validated

            # Validate tool calls
            if update.tool_calls:
                for tool_call in update.tool_calls:
                    tool_name = tool_call["name"]
                    valid, error = await self.tool_monitor.validate_tool_call(
                        tool_name,
                        tool_call.get("input", {}),
                        working_directory,
                        user_id,
                    )

                    if not valid:
                        tools_validated = False
                        validation_errors.append(error)

                        # Track blocked tools
                        if "Tool not allowed:" in error:
                            blocked_tools.add(tool_name)

                        logger.error(
                            "Tool validation failed",
                            tool_name=tool_name,
                            error=error,
                            user_id=user_id,
                        )

                        # For critical tools, we should fail fast
                        if tool_name in ["Task", "Read", "Write", "Edit"]:
                            # Create comprehensive error message
                            admin_instructions = self._get_admin_instructions(
                                list(blocked_tools)
                            )
                            error_msg = self._create_tool_error_message(
                                list(blocked_tools),
                                self.config.claude_allowed_tools or [],
                                admin_instructions,
                            )

                            raise ClaudeToolValidationError(
                                error_msg,
                                blocked_tools=list(blocked_tools),
                                allowed_tools=self.config.claude_allowed_tools or [],
                            )

            # Pass to caller's handler
            if on_stream:
                try:
                    await on_stream(update)
                except Exception as e:
                    logger.warning("Stream callback failed", error=str(e))

        # Execute command
        try:
            # Only continue session if it's not a new session
            should_continue = bool(session_id) and not getattr(
                session, "is_new_session", False
            )

            # For new sessions, don't pass the temporary session_id to Claude Code
            claude_session_id = (
                None
                if getattr(session, "is_new_session", False)
                else session.session_id
            )

            response = await self._execute_with_fallback(
                prompt=prompt,
                working_directory=working_directory,
                session_id=claude_session_id,
                continue_session=should_continue,
                stream_callback=stream_handler,
            )

            # Check if tool validation failed
            if not tools_validated:
                logger.error(
                    "Command completed but tool validation failed",
                    validation_errors=validation_errors,
                )
                # Mark response as having errors and include validation details
                response.is_error = True
                response.error_type = "tool_validation_failed"

                # Extract blocked tool names for user feedback
                blocked_tools = []
                for error in validation_errors:
                    if "Tool not allowed:" in error:
                        tool_name = error.split("Tool not allowed: ")[1]
                        blocked_tools.append(tool_name)

                # Create user-friendly error message
                if blocked_tools:
                    tool_list = ", ".join(f"`{tool}`" for tool in blocked_tools)
                    response.content = (
                        f"🚫 **Tool Access Blocked**\n\n"
                        f"Claude tried to use tools not allowed:\n"
                        f"{tool_list}\n\n"
                        f"**What you can do:**\n"
                        f"• Contact the administrator to request access to these tools\n"
                        f"• Try rephrasing your request to use different approaches\n"
                        f"• Check what tools are currently available with `/status`\n\n"
                        f"**Currently allowed tools:**\n"
                        f"{', '.join(f'`{t}`' for t in self.config.claude_allowed_tools or [])}"
                    )
                else:
                    response.content = (
                        f"🚫 **Tool Validation Failed**\n\n"
                        f"Tools failed security validation. Try different approach.\n\n"
                        f"Details: {'; '.join(validation_errors)}"
                    )

            # Update session (this may change the session_id for new sessions)
            old_session_id = session.session_id
            await self.session_manager.update_session(session.session_id, response)

            # For new sessions, get the updated session_id from the session manager
            if hasattr(session, "is_new_session") and response.session_id:
                # The session_id has been updated to Claude's session_id
                final_session_id = response.session_id
            else:
                # Use the original session_id for continuing sessions
                final_session_id = old_session_id

            # Ensure response has the correct session_id
            response.session_id = final_session_id

            logger.info(
                "Claude command completed",
                session_id=response.session_id,
                cost=response.cost,
                duration_ms=response.duration_ms,
                num_turns=response.num_turns,
                is_error=response.is_error,
            )

            return response

        except Exception as e:
            logger.error(
                "Claude command failed",
                error=str(e),
                user_id=user_id,
                session_id=session.session_id,
            )
            raise

    async def _execute_with_fallback(
        self,
        prompt: str,
        working_directory: Path,
        session_id: Optional[str] = None,
        continue_session: bool = False,
        stream_callback: Optional[Callable] = None,
    ) -> ClaudeResponse:
        """Execute command with Agent SDK as primary, subprocess as fallback."""
        # Use Agent SDK if available (preferred)
        if self.agent_integration and self.agent_integration.is_sdk_available:
            try:
                logger.debug("Attempting Agent SDK execution")

                # Collect response from async generator
                content_parts = []
                tools_used = []
                final_session_id = session_id or ""
                cost = 0.0

                # Convert stream callback for agent integration
                async def agent_stream_handler(update: AgentStreamUpdate):
                    if stream_callback:
                        # Convert AgentStreamUpdate to legacy StreamUpdate
                        legacy_update = StreamUpdate(
                            content=update.content or "",
                            tool_calls=(
                                [{"name": update.tool_name, "input": update.tool_input}]
                                if update.tool_name
                                else []
                            ),
                        )
                        try:
                            result = stream_callback(legacy_update)
                            if hasattr(result, "__await__"):
                                await result
                        except Exception as e:
                            logger.warning("Stream callback failed", error=str(e))

                # Query agent integration
                async for response in self.agent_integration.query(
                    user_id=0,  # Will be set by session manager
                    prompt=prompt,
                    stream_callback=agent_stream_handler,
                ):
                    if response.get("type") == "text":
                        content_parts.append(response.get("content", ""))
                    elif response.get("type") == "tool_use":
                        tools_used.append(
                            {
                                "name": response.get("tool_name"),
                                "input": response.get("tool_input"),
                            }
                        )
                    elif response.get("type") == "complete":
                        cost = response.get("cost", 0.0)
                        if response.get("session_id"):
                            final_session_id = response.get("session_id")
                    elif response.get("type") == "error":
                        # Return error response
                        return ClaudeResponse(
                            content=response.get("content", "Unknown error"),
                            session_id=final_session_id,
                            cost=0.0,
                            duration_ms=0,
                            num_turns=0,
                            is_error=True,
                            error_type=response.get("error_type", "agent_error"),
                        )

                # Build final response
                self._sdk_failed_count = 0
                return ClaudeResponse(
                    content="\n".join(content_parts) if content_parts else "",
                    session_id=final_session_id,
                    cost=cost,
                    duration_ms=0,
                    num_turns=1,
                    is_error=False,
                    tools_used=tools_used,
                )

            except Exception as e:
                error_str = str(e)
                self._sdk_failed_count += 1
                logger.warning(
                    "Agent SDK failed, falling back to subprocess",
                    error=error_str,
                    failure_count=self._sdk_failed_count,
                    error_type=type(e).__name__,
                )

                # Use subprocess fallback
                try:
                    logger.info("Executing with subprocess fallback")
                    response = await self.process_manager.execute_command(
                        prompt=prompt,
                        working_directory=working_directory,
                        session_id=session_id,
                        continue_session=continue_session,
                        stream_callback=stream_callback,
                    )
                    logger.info("Subprocess fallback succeeded")
                    return response

                except Exception as fallback_error:
                    logger.error(
                        "Both Agent SDK and subprocess failed",
                        sdk_error=error_str,
                        subprocess_error=str(fallback_error),
                    )
                    raise e
        else:
            # Use subprocess directly if Agent SDK not available
            logger.debug("Using subprocess execution (Agent SDK not available)")
            return await self.process_manager.execute_command(
                prompt=prompt,
                working_directory=working_directory,
                session_id=session_id,
                continue_session=continue_session,
                stream_callback=stream_callback,
            )

    async def continue_session(
        self,
        user_id: int,
        working_directory: Path,
        prompt: Optional[str] = None,
        on_stream: Optional[Callable[[StreamUpdate], None]] = None,
    ) -> Optional[ClaudeResponse]:
        """Continue the most recent session."""
        logger.info(
            "Continuing session",
            user_id=user_id,
            working_directory=str(working_directory),
            has_prompt=bool(prompt),
        )

        # Get user's sessions
        sessions = await self.session_manager._get_user_sessions(user_id)

        # Find most recent session in this directory (exclude temporary sessions)
        matching_sessions = [
            s
            for s in sessions
            if s.project_path == working_directory
            and not s.session_id.startswith("temp_")
        ]

        if not matching_sessions:
            logger.info("No matching sessions found", user_id=user_id)
            return None

        # Get most recent
        latest_session = max(matching_sessions, key=lambda s: s.last_used)

        # Continue session
        return await self.run_command(
            prompt=prompt or "",
            working_directory=working_directory,
            user_id=user_id,
            session_id=latest_session.session_id,
            on_stream=on_stream,
        )

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        return await self.session_manager.get_session_info(session_id)

    async def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        sessions = await self.session_manager._get_user_sessions(user_id)
        return [
            {
                "session_id": s.session_id,
                "project_path": str(s.project_path),
                "created_at": s.created_at.isoformat(),
                "last_used": s.last_used.isoformat(),
                "total_cost": s.total_cost,
                "message_count": s.message_count,
                "tools_used": s.tools_used,
                "expired": s.is_expired(self.config.session_timeout_hours),
            }
            for s in sessions
        ]

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        return await self.session_manager.cleanup_expired_sessions()

    async def get_tool_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics."""
        return self.tool_monitor.get_tool_stats()

    async def get_user_summary(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user summary."""
        session_summary = await self.session_manager.get_user_session_summary(user_id)
        tool_usage = self.tool_monitor.get_user_tool_usage(user_id)

        return {
            "user_id": user_id,
            **session_summary,
            **tool_usage,
        }

    async def shutdown(self) -> None:
        """Shutdown integration and cleanup resources."""
        logger.info("Shutting down Claude integration")

        # Close Agent SDK sessions
        if self.agent_integration:
            await self.agent_integration.close_all()

        # Kill any active processes (legacy managers)
        if hasattr(self.manager, "kill_all_processes"):
            await self.manager.kill_all_processes()

        # Clean up expired sessions
        await self.cleanup_expired_sessions()

        logger.info("Claude integration shutdown complete")

    def _get_admin_instructions(self, blocked_tools: List[str]) -> str:
        """Generate admin instructions for enabling blocked tools."""
        instructions = []

        # Check if settings file exists
        settings_file = Path(".env")

        if blocked_tools:
            # Get current allowed tools and create merged list without duplicates
            current_tools = [
                "Read",
                "Write",
                "Edit",
                "Bash",
                "Glob",
                "Grep",
                "LS",
                "Task",
                "MultiEdit",
                "NotebookRead",
                "NotebookEdit",
                "WebFetch",
                "TodoRead",
                "TodoWrite",
                "WebSearch",
            ]
            merged_tools = list(
                dict.fromkeys(current_tools + blocked_tools)
            )  # Remove duplicates while preserving order
            merged_tools_str = ",".join(merged_tools)
            merged_tools_py = ", ".join(f'"{tool}"' for tool in merged_tools)

            instructions.append("**For Administrators:**")
            instructions.append("")

            if settings_file.exists():
                instructions.append(
                    "To enable these tools, add them to your `.env` file:"
                )
                instructions.append("```")
                instructions.append(f'CLAUDE_ALLOWED_TOOLS="{merged_tools_str}"')
                instructions.append("```")
            else:
                instructions.append("To enable these tools:")
                instructions.append("1. Create a `.env` file in your project root")
                instructions.append("2. Add the following line:")
                instructions.append("```")
                instructions.append(f'CLAUDE_ALLOWED_TOOLS="{merged_tools_str}"')
                instructions.append("```")

            instructions.append("")
            instructions.append("Or modify the default in `src/config/settings.py`:")
            instructions.append("```python")
            instructions.append("claude_allowed_tools: Optional[List[str]] = Field(")
            instructions.append(f"    default=[{merged_tools_py}],")
            instructions.append('    description="List of allowed Claude tools",')
            instructions.append(")")
            instructions.append("```")

        return "\n".join(instructions)

    def _create_tool_error_message(
        self,
        blocked_tools: List[str],
        allowed_tools: List[str],
        admin_instructions: str,
    ) -> str:
        """Create a comprehensive error message for tool validation failures."""
        tool_list = ", ".join(f"`{tool}`" for tool in blocked_tools)
        allowed_list = (
            ", ".join(f"`{tool}`" for tool in allowed_tools)
            if allowed_tools
            else "None"
        )

        message = [
            "🚫 **Tool Access Blocked**",
            "",
            f"Claude tried to use tools that are not currently allowed:",
            f"{tool_list}",
            "",
            "**Why this happened:**",
            "• Claude needs these tools to complete your request",
            "• These tools are not in the allowed tools list",
            "• This is a security feature to control what Claude can do",
            "",
            "**What you can do:**",
            "• Contact the administrator to request access to these tools",
            "• Try rephrasing your request to use different approaches",
            "• Use simpler requests that don't require these tools",
            "",
            "**Currently allowed tools:**",
            f"{allowed_list}",
            "",
            admin_instructions,
        ]

        return "\n".join(message)
