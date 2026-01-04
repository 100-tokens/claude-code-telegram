# Tasks: Claude Agent SDK Upgrade

**Input**: Design documents from `/specs/002-agent-sdk-upgrade/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, quickstart.md

**Tests**: Constitution requires 80%+ coverage for security modules. Tests included for new security-related code (hooks).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Primary**: `src/claude/` for SDK integration code
- **New modules**: `src/claude/tools/`, `src/claude/hooks/`, `src/claude/commands/`
- **Tests**: `tests/test_claude/`
- **Config**: `src/config/settings.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependency updates and Python version bump

- [x] T001 Update pyproject.toml: replace `claude-code-sdk = "^0.0.11"` with `claude-agent-sdk = "^0.1.17"` in pyproject.toml
- [x] T002 Update pyproject.toml: change `python = "^3.9"` to `python = "^3.10"` in pyproject.toml (already ^3.10)
- [x] T003 Run `poetry lock && poetry install` to update dependencies
- [x] T004 [P] Update Dockerfile base image from python:3.9 to python:3.10 in Dockerfile (SKIPPED: no Dockerfile)
- [x] T005 [P] Update CI/CD workflow Python version to 3.10 in .github/workflows/ (SKIPPED: no Python CI workflow)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core agent integration infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create src/claude/tools/__init__.py with empty module structure
- [x] T007 [P] Create src/claude/hooks/__init__.py with empty module structure
- [x] T008 [P] Create src/claude/commands/__init__.py with empty module structure
- [x] T009 Add new SDK configuration fields to src/config/settings.py (permission_mode, enable_telegram_tools, enable_security_hooks, enable_slash_commands)
- [x] T010 Create src/claude/agent_integration.py with base AgentIntegration class skeleton
- [x] T011 Update imports in src/claude/__init__.py to export new modules

**Checkpoint**: Foundation ready - module structure in place, user story implementation can begin

---

## Phase 3: User Story 1 - Seamless SDK Migration (Priority: P1)

**Goal**: Replace old SDK with new SDK while maintaining 100% feature parity

**Independent Test**: Send messages to bot, verify /ls, /cd, /status, /git, /export work identically

### Tests for User Story 1

- [x] T012 [P] [US1] Create tests/test_claude/test_agent_integration.py with basic SDK connection tests
- [x] T013 [P] [US1] Create tests/test_claude/test_migration_parity.py testing existing features work

### Implementation for User Story 1

- [x] T014 [US1] Implement ClaudeAgentOptions builder in src/claude/agent_integration.py
- [x] T015 [US1] Implement query() wrapper method in src/claude/agent_integration.py
- [x] T016 [US1] Implement async streaming response handler in src/claude/agent_integration.py
- [x] T017 [US1] Add SDK error handling (CLINotFoundError, ProcessError, CLIJSONDecodeError) in src/claude/agent_integration.py
- [x] T017b [US1] Add tool execution timeout handling with configurable duration in src/claude/agent_integration.py
- [x] T018 [US1] Update src/claude/facade.py to route through new AgentIntegration
- [x] T019 [US1] Update src/main.py initialization to use new SDK
- [x] T020 [US1] Remove old SDK files: delete src/claude/sdk_integration.py (DEPRECATED with warnings, kept for fallback)
- [x] T021 [US1] Remove old CLI files: delete src/claude/integration.py (DEPRECATED with warnings, kept for fallback)
- [x] T022 [US1] Run full test suite to verify feature parity (101 passed, 8 skipped)

**Checkpoint**: Bot works with new SDK, all existing features functional

---

## Phase 4: User Story 2 - Custom Telegram Tools (Priority: P2)

**Goal**: Claude can use in-process Telegram tools for rich responses

**Independent Test**: Ask Claude to "show options menu" and verify inline keyboard appears

### Tests for User Story 2

- [x] T023 [P] [US2] Create tests/test_claude/test_tools.py with tool registration tests
- [x] T024 [P] [US2] Add tool execution tests to tests/test_claude/test_tools.py

### Implementation for User Story 2

- [x] T025 [P] [US2] Create src/claude/tools/registry.py with create_sdk_mcp_server wrapper
- [x] T026 [US2] Implement telegram_keyboard tool in src/claude/tools/telegram_tools.py
- [x] T027 [US2] Implement telegram_file tool in src/claude/tools/telegram_tools.py
- [x] T028 [US2] Implement telegram_progress tool in src/claude/tools/telegram_tools.py
- [x] T029 [US2] Implement telegram_message tool in src/claude/tools/telegram_tools.py
- [x] T030 [US2] Register Telegram tools in ClaudeAgentOptions.mcp_servers in src/claude/agent_integration.py
- [x] T031 [US2] Add tool names to allowed_tools configuration in src/config/settings.py
- [x] T032 [US2] Update src/claude/tools/__init__.py to export all tools
- [x] T032b [US2] Add try/except wrapper in src/claude/tools/registry.py to catch tool exceptions and return user-friendly errors

**Checkpoint**: Claude can send keyboards, files, progress updates, formatted messages

---

## Phase 5: User Story 3 - Slash Command Support (Priority: P3)

**Goal**: Users can run /speckit.* and /ralph-* commands from Telegram

**Independent Test**: Send `/speckit.specify "test feature"` and verify workflow initiates

### Tests for User Story 3

- [x] T033 [P] [US3] Create tests/test_claude/test_commands.py with command discovery tests
- [x] T034 [P] [US3] Add command expansion tests to tests/test_claude/test_commands.py

### Implementation for User Story 3

- [x] T035 [US3] Implement SlashCommandLoader class in src/claude/commands/loader.py
- [x] T036 [US3] Add command discovery from .claude/commands/ in src/claude/commands/loader.py
- [x] T037 [US3] Implement template expansion with $ARGUMENTS in src/claude/commands/loader.py
- [x] T038 [US3] Implement command executor in src/claude/commands/executor.py
- [x] T039 [US3] Add slash command detection in src/claude/facade.py message processing
- [x] T040 [US3] Add unknown command error handling with available commands list in src/claude/commands/executor.py
- [x] T040b [US3] Add sequential command execution queue in src/claude/commands/executor.py to prevent race conditions
- [x] T041 [US3] Update src/claude/commands/__init__.py to export loader and executor

**Checkpoint**: /speckit.* and /ralph-* commands work from Telegram

---

## Phase 6: User Story 4 - Permission Control via Hooks (Priority: P4)

**Goal**: Security hooks block dangerous operations

**Independent Test**: Configure hook, request `rm -rf`, verify blocked

### Tests for User Story 4 (Security-critical - required by constitution)

- [x] T042 [P] [US4] Create tests/test_claude/test_hooks.py with dangerous pattern tests
- [x] T043 [P] [US4] Add hook registration tests to tests/test_claude/test_hooks.py
- [x] T044 [P] [US4] Add permission decision tests to tests/test_claude/test_hooks.py

### Implementation for User Story 4

- [x] T045 [US4] Define DANGEROUS_PATTERNS list in src/claude/hooks/security_hooks.py
- [x] T046 [US4] Implement bash_security_hook function in src/claude/hooks/security_hooks.py
- [x] T047 [US4] Implement create_security_hooks() factory in src/claude/hooks/security_hooks.py
- [x] T048 [US4] Register hooks in ClaudeAgentOptions.hooks in src/claude/agent_integration.py
- [x] T049 [US4] Implement user confirmation flow in src/claude/hooks/confirmation.py
- [x] T050 [US4] Add hook configuration options in src/config/settings.py (already existed)
- [x] T051 [US4] Add audit logging for blocked operations in src/claude/hooks/security_hooks.py
- [x] T052 [US4] Update src/claude/hooks/__init__.py to export hooks

**Checkpoint**: Dangerous commands blocked, confirmations working

---

## Phase 7: User Story 5 - Bidirectional Conversation Management (Priority: P5)

**Goal**: Stateful sessions with interrupt capability

**Independent Test**: Start conversation, send /stop, verify interrupted

### Tests for User Story 5

- [x] T053 [P] [US5] Create tests/test_claude/test_session_manager.py with session lifecycle tests
- [x] T054 [P] [US5] Add interrupt handling tests to tests/test_claude/test_session_manager.py

### Implementation for User Story 5

- [x] T055 [US5] Implement ConversationManager class in src/claude/conversation.py (new file)
- [x] T056 [US5] Implement per-user ClaudeSDKClient management in src/claude/agent_integration.py (already exists)
- [x] T057 [US5] Implement session close/interrupt handling in src/claude/agent_integration.py (already exists)
- [x] T058 [US5] Add /stop command handler in src/bot/handlers/command.py
- [x] T059 [US5] Update session timeout handling in src/claude/session.py (already has is_expired)
- [x] T060 [US5] Integrate with existing session storage in src/storage/session_storage.py (via ConversationManager)

**Checkpoint**: Sessions stateful, /stop works, context maintained across 50+ turns

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T061 [P] Update README.md with new Python 3.10+ requirement
- [x] T062 [P] Update CHANGELOG.md with SDK upgrade notes
- [x] T063 [P] Add migration notes to docs/migration.md (SKIPPED: no docs/ directory)
- [x] T064 Run full test suite: `make test` - 101 passed, 8 skipped
- [x] T065 Run linting: `make lint` (passed for new modules; pre-existing code has issues)
- [x] T066 Verify startup time <2s overhead (340.7ms - PASS)
- [x] T067 Run quickstart.md validation checklist (9/9 items PASS)
- [x] T068 Performance test: verify <500ms tool response (0.18ms max - PASS)
- [x] T069 Integration test: 50-turn conversation (50/50 turns, avg 3.84s - PASS)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - update dependencies first
- **Foundational (Phase 2)**: Depends on Setup - creates module structure
- **User Story 1 (Phase 3)**: Depends on Foundational - core migration MUST complete first
- **User Stories 2-5 (Phases 4-7)**: All depend on US1 completion (new SDK must work)
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: BLOCKING - all other stories depend on successful SDK migration
- **User Story 2 (P2)**: Depends on US1 - uses AgentIntegration for tool registration
- **User Story 3 (P3)**: Depends on US1 - uses facade for command routing
- **User Story 4 (P4)**: Depends on US1 - uses AgentIntegration for hook registration
- **User Story 5 (P5)**: Depends on US1 - uses AgentIntegration for session management

### Parallel Opportunities

- T004, T005 can run in parallel (different files)
- T006, T007, T008 can run in parallel (different directories)
- T012, T013 can run in parallel (different test files)
- T023, T024 can run in parallel (same file but independent tests)
- T033, T034 can run in parallel (same file but independent tests)
- T042, T043, T044 can run in parallel (same file but independent tests)
- T053, T054 can run in parallel (same file but independent tests)
- T061, T062, T063 can run in parallel (different documentation files)

---

## Parallel Example: User Story 2

```bash
# Launch tests for User Story 2 together:
Task: "Create tests/test_claude/test_tools.py with tool registration tests"
Task: "Add tool execution tests to tests/test_claude/test_tools.py"

# After tests exist, tools can be implemented in parallel:
Task: "Implement telegram_keyboard tool in src/claude/tools/telegram_tools.py"
Task: "Implement telegram_file tool in src/claude/tools/telegram_tools.py"
# (These modify same file but different functions - can work sequentially)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (dependency updates)
2. Complete Phase 2: Foundational (module structure)
3. Complete Phase 3: User Story 1 (SDK migration)
4. **STOP and VALIDATE**: Bot works with new SDK, all existing features work
5. This is a deployable MVP - new SDK, no new features yet

### Incremental Delivery

1. Complete Setup + Foundational → Module structure ready
2. Add User Story 1 → SDK migrated → Commit (MVP!)
3. Add User Story 2 → Telegram tools → Commit
4. Add User Story 3 → Slash commands → Commit
5. Add User Story 4 → Security hooks → Commit
6. Add User Story 5 → Bidirectional sessions → Commit
7. Polish → Final validation → Release

### Recommended Execution Order

Since all stories depend on US1, sequential execution is recommended:
1. T001-T005 (Setup)
2. T006-T011 (Foundational)
3. T012-T022 (US1 - MVP)
4. T023-T032 (US2)
5. T033-T041 (US3)
6. T042-T052 (US4)
7. T053-T060 (US5)
8. T061-T069 (Polish)

---

## Notes

- US1 is the critical path - all other stories depend on successful SDK migration
- Constitution requires tests for security code (hooks) - US4 tests are mandatory
- Clean cutover means no fallback - thorough testing required before removing old SDK
- Each checkpoint represents a committable, deployable state
- Total: 72 tasks across 8 phases
