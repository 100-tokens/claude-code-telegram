# Implementation Plan: CLI Bot Launcher

**Branch**: `003-cli-bot-launcher` | **Date**: 2026-01-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-cli-bot-launcher/spec.md`

## Summary

Create a CLI that allows users to start the Telegram bot from any directory, using the current working directory as the approved directory for file operations. The existing `src/main.py` already provides most functionality; this enhancement adds current-directory detection and improved startup messaging.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: python-telegram-bot, structlog, pydantic-settings, click (new, for enhanced CLI)
**Storage**: SQLite via aiosqlite (existing)
**Testing**: pytest with pytest-asyncio
**Target Platform**: Linux/macOS/Windows (cross-platform CLI)
**Project Type**: Single project (existing structure)
**Performance Goals**: <5 seconds startup to "ready" status
**Constraints**: Must work without modifying user's `.env` file
**Scale/Scope**: Single bot instance, single user at a time

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Security-First Design | ✅ PASS | Directory sandboxing preserved - CWD becomes approved directory |
| II. Async-First Architecture | ✅ PASS | No changes to async patterns |
| III. Clean Separation of Concerns | ✅ PASS | CLI layer remains in entry point |
| IV. Test-First Development | ✅ PASS | Unit tests for CLI argument handling |
| V. User Experience Focus | ✅ PASS | Clear startup messages, error guidance |
| VI. Defensive Cost Management | ✅ PASS | No changes to cost controls |

**Gate Result**: PASS - No violations

## Project Structure

### Documentation (this feature)

```text
specs/003-cli-bot-launcher/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── __init__.py          # Contains __version__
├── main.py              # CLI entry point (MODIFY)
├── cli/                 # NEW: CLI module
│   ├── __init__.py
│   └── commands.py      # CLI command definitions
├── bot/                 # Existing bot handlers
├── claude/              # Existing Claude integration
├── config/              # Existing configuration
├── security/            # Existing security layer
└── storage/             # Existing storage layer

tests/
├── unit/
│   └── test_cli/        # NEW: CLI unit tests
│       ├── __init__.py
│       └── test_commands.py
└── integration/
```

**Structure Decision**: Extend existing single-project structure with new `src/cli/` module for CLI-specific logic, keeping `src/main.py` as the entry point.

## Complexity Tracking

> No Constitution Check violations - this section is empty.

## Design Decisions

### DD-001: CLI Framework Choice

**Decision**: Use `click` library for CLI implementation
**Rationale**:
- More feature-rich than `argparse` for complex CLIs
- Better help text formatting and colored output
- Supports command groups for future expansion
- Well-maintained and widely adopted

**Alternative Rejected**: Keep `argparse`
- Sufficient for current needs but less extensible
- No colored output or rich formatting

### DD-002: Current Directory Detection

**Decision**: Use `pathlib.Path.cwd()` to detect current directory and set as `APPROVED_DIRECTORY`
**Rationale**:
- Standard Python approach, cross-platform
- Explicit and predictable behavior
- Can be overridden via `--directory` flag

### DD-003: Configuration Priority

**Decision**: CLI arguments > Environment variables > `.env` file defaults
**Rationale**:
- Standard convention for CLI tools
- Allows flexible deployment scenarios
- Preserves backward compatibility

## Implementation Approach

### Phase 1: Minimal CLI Enhancement

1. Add `--directory` flag to specify working directory (defaults to CWD)
2. Override `APPROVED_DIRECTORY` from CLI flag before config load
3. Display startup banner with bot info and approved directory

### Phase 2: Enhanced Error Handling

1. Validate directory exists and is readable before startup
2. Check for `.env` file presence with helpful error message
3. Validate minimum required configuration early

### Phase 3: Status Display

1. Show formatted startup banner with:
   - Bot username
   - Approved directory
   - Enabled features
   - SDK status
2. Show graceful shutdown message with session cleanup stats

## Dependencies

### New Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| click | ^8.1.0 | CLI framework with rich help text |
| rich | ^13.0.0 | Terminal formatting and colors (optional) |

### Existing Dependencies (no changes)

- python-telegram-bot: Telegram integration
- structlog: Structured logging
- pydantic-settings: Configuration management
