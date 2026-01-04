# Tasks: CLI Bot Launcher

**Input**: Design documents from `/specs/003-cli-bot-launcher/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: Not explicitly requested in specification. Tests omitted from task list.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add click dependency and create CLI module structure

- [x] T001 Add click ^8.1.0 to pyproject.toml dependencies
- [x] T002 Run `poetry install` to install new dependency
- [x] T003 [P] Create src/cli/__init__.py with module docstring
- [x] T004 [P] Create src/cli/display.py for banner and output formatting

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core CLI infrastructure that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create src/cli/commands.py with click group and base structure
- [x] T006 Implement directory validation helper in src/cli/commands.py
- [x] T007 Implement config validation helper in src/cli/commands.py
- [x] T008 Update src/main.py to use click-based CLI from src/cli/commands.py
- [x] T009 Update pyproject.toml entry point to use new CLI module

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Start Bot from Current Directory (Priority: P1) 🎯 MVP

**Goal**: User can run CLI command to start bot using current directory as approved directory

**Independent Test**: Run `claude-telegram-bot` in a configured directory, verify bot starts and responds to Telegram messages

### Implementation for User Story 1

- [x] T010 [US1] Implement `--directory` option in src/cli/commands.py (defaults to CWD via Path.cwd().resolve())
- [x] T011 [US1] Implement directory override logic to set APPROVED_DIRECTORY env var before config load in src/cli/commands.py
- [x] T012 [US1] Implement start command that calls existing main() logic in src/cli/commands.py
- [x] T013 [US1] Add .env file detection and loading from specified directory in src/cli/commands.py
- [x] T014 [US1] Verify startup works with current directory as approved directory

**Checkpoint**: User Story 1 complete - bot can start from current directory

---

## Phase 4: User Story 2 - Configuration Validation on Startup (Priority: P1)

**Goal**: CLI validates config and displays clear error messages for missing/invalid configuration

**Independent Test**: Run CLI with missing .env or invalid config, verify clear error messages are displayed

### Implementation for User Story 2

- [x] T015 [US2] Create ConfigError exception class in src/cli/errors.py
- [x] T016 [US2] Implement .env file existence check with user-friendly error in src/cli/commands.py
- [x] T017 [US2] Implement TELEGRAM_BOT_TOKEN missing check with guidance message in src/cli/commands.py
- [x] T018 [US2] Wrap pydantic validation errors with user-friendly messages in src/cli/commands.py
- [x] T019 [US2] Add error message formatting with "To fix:" guidance in src/cli/display.py

**Checkpoint**: User Story 2 complete - config errors show clear guidance

---

## Phase 5: User Story 3 - Graceful Shutdown (Priority: P2)

**Goal**: Ctrl+C cleanly shuts down bot and displays confirmation

**Independent Test**: Start bot, press Ctrl+C, verify clean shutdown message appears

### Implementation for User Story 3

- [x] T020 [US3] Implement shutdown message display in src/cli/display.py
- [x] T021 [US3] Add session cleanup stats to shutdown message in src/cli/commands.py
- [x] T022 [US3] Ensure KeyboardInterrupt is caught and displays friendly message

**Checkpoint**: User Story 3 complete - graceful shutdown with confirmation

---

## Phase 6: User Story 4 - Display Bot Status Information (Priority: P2)

**Goal**: Startup banner shows bot username, approved directory, and enabled features

**Independent Test**: Start bot, verify banner displays with correct information

### Implementation for User Story 4

- [x] T023 [US4] Implement startup banner function in src/cli/display.py with box formatting
- [x] T024 [US4] Add bot username display to banner (fetched after Telegram connection)
- [x] T025 [US4] Add approved directory display to banner
- [x] T026 [US4] Add enabled features list to banner (SDK, Git, Quick Actions, etc.)
- [x] T027 [US4] Add "Ready" status indicator to banner
- [x] T028 [US4] Integrate banner display into startup sequence in src/cli/commands.py

**Checkpoint**: User Story 4 complete - startup shows informative banner

---

## Phase 7: User Story 5 - Version and Help Information (Priority: P3)

**Goal**: CLI supports --version and --help flags

**Independent Test**: Run `claude-telegram-bot --version` and `--help`, verify correct output

### Implementation for User Story 5

- [x] T029 [US5] Add --version flag using click.version_option in src/cli/commands.py
- [x] T030 [US5] Customize help text for all options in src/cli/commands.py
- [x] T031 [US5] Add descriptive docstring to CLI group for help output

**Checkpoint**: User Story 5 complete - version and help work correctly

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and validation

- [x] T032 [P] Update README.md with new CLI usage examples
- [x] T033 [P] Add CLI usage to quickstart documentation
- [x] T034 Run quickstart.md validation checklist
- [x] T035 Verify all existing tests still pass with `make test`
- [x] T036 Run `make lint` and fix any issues (CLI module passes; pre-existing errors in other files)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 priority but US1 is the true MVP
  - US3-US5 can proceed after US1/US2
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: MVP - No dependencies on other stories
- **User Story 2 (P1)**: Can run parallel to US1, independent validation logic
- **User Story 3 (P2)**: Depends on US1 (needs running bot to shutdown)
- **User Story 4 (P2)**: Depends on US1 (needs running bot to display status)
- **User Story 5 (P3)**: No dependencies - can run parallel after Foundation

### Parallel Opportunities

Within Phase 1:
- T003 and T004 can run in parallel (different files)

Within Phase 8:
- T032 and T033 can run in parallel (different files)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T009)
3. Complete Phase 3: User Story 1 (T010-T014)
4. **STOP and VALIDATE**: Test bot starts from current directory
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Bot starts from CWD (MVP!)
3. Add User Story 2 → Clear config error messages
4. Add User Story 3 → Graceful shutdown
5. Add User Story 4 → Informative startup banner
6. Add User Story 5 → Version and help flags
7. Polish → Documentation and cleanup

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Existing src/main.py logic should be preserved and wrapped by CLI
- Click decorators handle --help automatically
- Use click.echo() for output instead of print()
- Exit codes: 0 = success, 1 = config error, 2 = runtime error
