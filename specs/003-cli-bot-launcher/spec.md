# Feature Specification: CLI Bot Launcher

**Feature Branch**: `003-cli-bot-launcher`
**Created**: 2026-01-04
**Status**: Draft
**Input**: User description: "I would like to create a CLI that could start the bot from the current directory."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start Bot from Current Directory (Priority: P1)

A developer navigates to a project directory containing a valid configuration and runs a simple command to start the Telegram bot. The bot initializes using the current directory as the approved directory and begins accepting messages.

**Why this priority**: This is the core functionality - the primary reason for the CLI. Without this, no other features matter.

**Independent Test**: Can be tested by running the CLI command in a configured directory and verifying the bot starts and responds to Telegram messages.

**Acceptance Scenarios**:

1. **Given** the user is in a directory with a valid `.env` file containing required configuration, **When** the user runs the CLI start command, **Then** the bot starts successfully and displays startup confirmation.
2. **Given** the user is in a directory with a valid configuration, **When** the bot starts successfully, **Then** the current directory is used as the approved directory for file operations.
3. **Given** the bot has started, **When** the user sends a message via Telegram, **Then** the bot responds appropriately.

---

### User Story 2 - Configuration Validation on Startup (Priority: P1)

Before starting, the CLI validates that all required configuration is present and valid. If configuration is missing or invalid, the CLI provides clear error messages indicating what needs to be fixed.

**Why this priority**: Critical for user experience - users must understand why startup fails and how to fix it.

**Independent Test**: Can be tested by running the CLI with missing or invalid configuration and verifying appropriate error messages are displayed.

**Acceptance Scenarios**:

1. **Given** the user is in a directory without a `.env` file, **When** the user runs the CLI start command, **Then** the CLI displays a clear error message indicating the missing configuration file.
2. **Given** the `.env` file is missing the Telegram bot token, **When** the user runs the CLI start command, **Then** the CLI displays an error specifying the missing `TELEGRAM_BOT_TOKEN`.
3. **Given** the configuration contains an invalid value, **When** the user runs the CLI start command, **Then** the CLI displays a validation error with guidance on valid values.

---

### User Story 3 - Graceful Shutdown (Priority: P2)

The user can stop the running bot gracefully using keyboard interrupt (Ctrl+C). The bot cleanly shuts down, closes connections, and saves any pending state.

**Why this priority**: Important for proper resource management but secondary to core startup functionality.

**Independent Test**: Can be tested by starting the bot, pressing Ctrl+C, and verifying clean shutdown without errors.

**Acceptance Scenarios**:

1. **Given** the bot is running, **When** the user presses Ctrl+C, **Then** the bot displays a shutdown message and terminates gracefully.
2. **Given** the bot has active sessions, **When** shutdown is initiated, **Then** all sessions are properly closed before termination.

---

### User Story 4 - Display Bot Status Information (Priority: P2)

When the bot starts, it displays useful status information including the bot username, approved directory, and enabled features. This helps users confirm the bot is configured correctly.

**Why this priority**: Enhances user experience and debugging but not essential for core functionality.

**Independent Test**: Can be tested by starting the bot and verifying status information is displayed.

**Acceptance Scenarios**:

1. **Given** the user starts the bot, **When** initialization completes, **Then** the CLI displays the bot username and approved directory.
2. **Given** the user starts the bot, **When** initialization completes, **Then** the CLI displays which features are enabled (SDK mode, MCP, etc.).

---

### User Story 5 - Version and Help Information (Priority: P3)

Users can display the CLI version and help information to understand available commands and options.

**Why this priority**: Standard CLI feature but lowest priority for MVP.

**Independent Test**: Can be tested by running version and help commands and verifying output.

**Acceptance Scenarios**:

1. **Given** the user runs the CLI with `--version` flag, **When** the command executes, **Then** the current version is displayed.
2. **Given** the user runs the CLI with `--help` flag, **When** the command executes, **Then** available commands and options are displayed.

---

### Edge Cases

- What happens when the user runs the CLI from a directory they don't have read permissions for?
- How does the CLI handle if the Telegram API is unreachable during startup?
- What happens if another instance of the bot is already running?
- How does the CLI behave if the `.env` file exists but is empty?
- What happens if the approved directory specified in config doesn't exist?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a command-line executable that can be invoked from any directory
- **FR-002**: System MUST use the current working directory as the default approved directory when starting
- **FR-003**: System MUST load configuration from a `.env` file in the current directory
- **FR-004**: System MUST validate all required configuration before attempting to start the bot
- **FR-005**: System MUST display clear error messages when configuration is missing or invalid
- **FR-006**: System MUST display startup status including bot username and approved directory
- **FR-007**: System MUST handle Ctrl+C interrupt and perform graceful shutdown
- **FR-008**: System MUST support `--version` flag to display version information
- **FR-009**: System MUST support `--help` flag to display usage information
- **FR-010**: System MUST exit with appropriate status codes (0 for success, non-zero for errors)

### Key Entities

- **CLI Entry Point**: The command-line interface that users invoke to start the bot
- **Configuration**: Settings loaded from environment files that control bot behavior
- **Bot Instance**: The running Telegram bot process that handles messages

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can start the bot with a single command in under 5 seconds from invocation to "ready" status
- **SC-002**: Configuration errors are detected and reported within 1 second of invocation
- **SC-003**: 100% of required configuration fields produce clear error messages when missing
- **SC-004**: Graceful shutdown completes within 5 seconds of Ctrl+C
- **SC-005**: Help output displays all available options and their descriptions

## Assumptions

- Users have a valid Telegram bot token obtained from BotFather
- The current directory structure follows the expected project layout
- Users have network access to the Telegram API
- The existing bot implementation (`src.main`) provides the core bot functionality
- Poetry is available for dependency management (standard for this project)

## Out of Scope

- Running multiple bot instances simultaneously
- Daemon/background mode (bot runs in foreground)
- Remote configuration fetching
- Automatic restart on failure
- Docker containerization (separate concern)
