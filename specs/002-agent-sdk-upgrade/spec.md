# Feature Specification: Claude Agent SDK Upgrade

**Feature Branch**: `002-agent-sdk-upgrade`
**Created**: 2025-01-04
**Status**: Draft
**Input**: User description: "Upgrade to Claude Agent SDK with in-process tools, hooks, and bidirectional conversations"

## Clarifications

### Session 2025-01-04

- Q: How should we handle Python 3.10+ requirement vs current 3.9 support? → A: Bump minimum Python version to 3.10+ (breaking change for 3.9 users)
- Q: Should the bot support dual SDK during migration? → A: Clean cutover - remove old SDK completely, new SDK only

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Seamless SDK Migration (Priority: P1)

The bot continues to function exactly as before but uses the new Claude Agent SDK (`claude-agent-sdk`) instead of the deprecated `claude-code-sdk`. All existing features (message handling, session management, file uploads, git integration) work identically from the user's perspective.

**Why this priority**: This is the foundation for all other improvements. Without a working migration, no new features can be added. Users should experience zero disruption.

**Independent Test**: Can be fully tested by sending messages to the bot and verifying all existing commands (/ls, /cd, /status, /git, /export) and Claude interactions work identically to before.

**Acceptance Scenarios**:

1. **Given** a user sends a text message, **When** the bot processes it through the new SDK, **Then** Claude responds with the same quality and format as before
2. **Given** a user uploads a file, **When** the bot processes it, **Then** the file is analyzed correctly using the new SDK
3. **Given** a user has an active session, **When** they continue the conversation, **Then** session context is maintained across messages
4. **Given** the bot starts up, **When** initialization completes, **Then** the new SDK connects successfully without requiring separate CLI installation

---

### User Story 2 - Custom Telegram Tools for Claude (Priority: P2)

Claude can use custom in-process tools that interact directly with Telegram, enabling richer responses. These tools allow Claude to send formatted messages, inline keyboards, progress updates, and file attachments directly through the bot.

**Why this priority**: This enables Claude to provide a native Telegram experience rather than plain text responses. It significantly improves user experience and enables interactive workflows.

**Independent Test**: Can be tested by asking Claude to "show me a menu of options" and verifying an inline keyboard appears, or asking Claude to "send this as a file" and receiving a downloadable attachment.

**Acceptance Scenarios**:

1. **Given** Claude wants to present options, **When** it uses the telegram_keyboard tool, **Then** the user sees an inline keyboard with clickable buttons
2. **Given** Claude generates a long code block, **When** it uses the telegram_file tool, **Then** the user receives a downloadable file attachment
3. **Given** Claude is processing a long task, **When** it uses the telegram_progress tool, **Then** the user sees real-time progress updates
4. **Given** Claude wants to format a message, **When** it uses the telegram_message tool with markdown, **Then** the user sees properly formatted text with bold, italic, code blocks, etc.

---

### User Story 3 - Slash Command Support from Telegram (Priority: P3)

Users can invoke Claude Code slash commands (like `/speckit.specify`, `/ralph-loop`) directly from Telegram. The bot detects these commands, loads the corresponding prompt templates, and sends the expanded prompts to Claude.

**Why this priority**: This bridges the gap between Claude Code's powerful workflow tools and remote Telegram access. Power users can run their full development workflow from mobile.

**Independent Test**: Can be tested by sending `/speckit.specify "add user login"` in Telegram and verifying the spec-kit workflow initiates with the proper prompt expansion.

**Acceptance Scenarios**:

1. **Given** a user sends `/speckit.specify "feature description"`, **When** the bot processes it, **Then** the spec-kit specify workflow starts with the full prompt template
2. **Given** a user sends `/ralph-loop "optimize code"`, **When** the bot processes it, **Then** the ralph-wiggum iterative loop begins
3. **Given** a user sends an unknown slash command, **When** the bot processes it, **Then** the user receives a helpful error listing available commands
4. **Given** command templates exist in `.claude/commands/`, **When** the bot starts, **Then** all available commands are discovered and registered

---

### User Story 4 - Permission Control via Hooks (Priority: P4)

Administrators can define security policies that intercept and control Claude's tool usage. Dangerous operations (like certain bash commands, file deletions, or git pushes) can be blocked or require confirmation before execution.

**Why this priority**: Enhances security beyond the current tool whitelist by allowing fine-grained control over what operations Claude can perform. Critical for enterprise deployments.

**Independent Test**: Can be tested by configuring a hook to block `rm -rf` commands and verifying Claude cannot execute them even if requested.

**Acceptance Scenarios**:

1. **Given** a hook blocks dangerous bash patterns, **When** Claude attempts to run `rm -rf /`, **Then** the operation is denied with a clear message
2. **Given** a hook requires confirmation for file writes, **When** Claude tries to write a file, **Then** the user is prompted to approve before execution
3. **Given** hooks are configured via environment variables or config file, **When** the bot starts, **Then** all hooks are registered and active
4. **Given** a hook denies an operation, **When** Claude receives the denial, **Then** it gracefully handles the rejection and informs the user

---

### User Story 5 - Bidirectional Conversation Management (Priority: P5)

The bot uses the new ClaudeSDKClient for stateful, bidirectional conversations instead of one-shot queries. This enables better session management, conversation forking, and the ability to interrupt or redirect Claude mid-response.

**Why this priority**: Improves conversation quality and control. Users can maintain longer, more coherent sessions and have better control over the AI's behavior.

**Independent Test**: Can be tested by starting a conversation, letting Claude work on a task, then sending a new message to redirect it, and verifying the context is maintained.

**Acceptance Scenarios**:

1. **Given** an active conversation, **When** the user sends a follow-up message, **Then** Claude maintains full context from previous exchanges
2. **Given** Claude is generating a long response, **When** the user sends `/stop`, **Then** the current generation is interrupted gracefully
3. **Given** multiple users are active, **When** they each converse with the bot, **Then** each user's session is isolated and stateful
4. **Given** a session times out, **When** the user returns, **Then** they can resume or start fresh with clear indication of state

---

### Edge Cases

- What happens when the Claude CLI bundled with the SDK has a different version than expected? System should log version info and continue with bundled CLI.
- How does the system handle tool execution timeouts? Operations should timeout after configured duration with user notification.
- What happens when a custom tool throws an exception? Error should be caught, logged, and user should see a friendly error message.
- How does the system behave when hooks block all tool usage? Claude should receive the blocked status and respond appropriately to the user.
- What happens when multiple slash commands are sent rapidly? Commands should queue and execute sequentially to prevent race conditions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace `claude-code-sdk` dependency with `claude-agent-sdk` package (clean cutover, no dual-SDK support)
- **FR-002**: System MUST use `ClaudeAgentOptions` for configuration instead of `ClaudeCodeOptions`
- **FR-003**: System MUST use the bundled Claude CLI from the SDK (no separate installation required)
- **FR-004**: System MUST support custom in-process MCP tools via `@tool` decorator and `create_sdk_mcp_server`
- **FR-005**: System MUST implement Telegram-specific tools (keyboard, file, progress, message formatting)
- **FR-006**: System MUST detect and expand slash commands from `.claude/commands/` directory
- **FR-007**: System MUST support `PreToolUse` hooks for permission control
- **FR-008**: System MUST use `ClaudeSDKClient` for bidirectional conversation management
- **FR-009**: System MUST maintain backward compatibility with all existing bot commands
- **FR-010**: System MUST handle all SDK error types (CLINotFoundError, ProcessError, CLIJSONDecodeError)
- **FR-011**: System MUST support the `permission_mode` configuration for auto-accepting or denying file edits
- **FR-012**: System MUST integrate with existing security middleware (auth, rate limiting, audit logging)

### Key Entities

- **CustomTool**: Represents an in-process tool with name, description, input schema, and async handler function
- **SlashCommand**: Represents a discovered command from `.claude/commands/` with name, template content, and metadata
- **Hook**: Represents a permission control function with matcher pattern and decision logic
- **ConversationSession**: Extended session model supporting bidirectional state management

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing bot functionality works identically after migration (100% feature parity)
- **SC-002**: Bot startup time does not increase by more than 2 seconds due to SDK changes
- **SC-003**: Custom Telegram tools respond within 500ms for simple operations (keyboard, formatting)
- **SC-004**: Slash commands from `.claude/commands/` are discoverable and executable within 1 second
- **SC-005**: Hook-based permission checks add no more than 100ms latency to tool execution
- **SC-006**: Session context is maintained across at least 50 conversation turns
- **SC-007**: Zero increase in error rate for Claude interactions compared to current SDK
- **SC-008**: Users can interrupt long-running operations within 2 seconds of sending stop command

## Assumptions

- The `claude-agent-sdk` package version 0.1.17+ is stable and production-ready
- The bundled CLI in the SDK package is functionally equivalent to the standalone Claude Code CLI
- Existing session storage schema in SQLite is compatible with new SDK session model
- Project minimum Python version will be upgraded from 3.9 to 3.10+ (breaking change accepted)
- MCP server tools registered via SDK are compatible with the existing tool monitoring/validation logic

## Out of Scope

- Mobile app development (Telegram-only interface)
- Web dashboard for administration
- Multi-tenant deployment with isolated configurations
- Real-time collaboration between multiple users on same session
- Voice/audio message processing
