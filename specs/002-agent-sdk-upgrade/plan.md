# Implementation Plan: Claude Agent SDK Upgrade

**Branch**: `002-agent-sdk-upgrade` | **Date**: 2025-01-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-agent-sdk-upgrade/spec.md`

## Summary

Upgrade the Claude integration layer from deprecated `claude-code-sdk` (0.0.11) to the new `claude-agent-sdk` (0.1.17+). This enables in-process custom tools, permission hooks, and bidirectional conversations. Key additions include Telegram-specific tools for richer UX, slash command support from `.claude/commands/`, and PreToolUse hooks for fine-grained security control.

## Technical Context

**Language/Version**: Python 3.10+ (upgraded from 3.9, breaking change accepted per clarification)
**Primary Dependencies**: claude-agent-sdk (0.1.17+), python-telegram-bot, aiosqlite, structlog
**Storage**: SQLite via aiosqlite (existing schema compatible)
**Testing**: pytest with pytest-asyncio, 80%+ coverage for security modules
**Target Platform**: Linux server (Docker), macOS for development
**Project Type**: Single Python application with Telegram bot interface
**Performance Goals**: <500ms tool response, <2s startup overhead, 50+ turn sessions
**Constraints**: Clean SDK cutover (no dual-SDK support), bundled CLI only
**Scale/Scope**: Single-tenant deployment, 10-50 concurrent users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Status | Notes |
|-----------|----------|--------|-------|
| I. Security-First Design | Yes | PASS | Hooks add defense layer; existing auth/rate-limiting preserved |
| II. Async-First Architecture | Yes | PASS | SDK uses async patterns; ClaudeSDKClient is async context manager |
| III. Clean Separation of Concerns | Yes | PASS | New tools in `src/claude/tools/`, hooks in `src/claude/hooks/` |
| IV. Test-First Development | Yes | PASS | Migration requires tests for SDK integration, tool execution |
| V. User Experience Focus | Yes | PASS | Custom Telegram tools improve UX; progress updates enabled |
| VI. Defensive Cost Management | Yes | PASS | Existing cost tracking compatible; session management enhanced |

**Gate Result**: PASS - All principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/002-agent-sdk-upgrade/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
├── checklists/          # Quality checklists
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── bot/                      # Existing - Telegram handlers (unchanged)
│   ├── handlers/
│   ├── middleware/
│   ├── features/
│   └── utils/
├── claude/                   # Modified - Claude integration layer
│   ├── agent_integration.py  # NEW: ClaudeSDKClient wrapper
│   ├── tools/                # NEW: Custom in-process MCP tools
│   │   ├── __init__.py
│   │   ├── telegram_tools.py # Keyboard, file, progress, message tools
│   │   └── registry.py       # Tool registration and discovery
│   ├── hooks/                # NEW: Permission control hooks
│   │   ├── __init__.py
│   │   ├── security_hooks.py # Dangerous pattern blocking
│   │   └── confirmation.py   # User confirmation flows
│   ├── commands/             # NEW: Slash command expansion
│   │   ├── __init__.py
│   │   ├── loader.py         # Load templates from .claude/commands/
│   │   └── executor.py       # Expand and execute commands
│   ├── sdk_integration.py    # REMOVE: Old claude-code-sdk integration
│   ├── integration.py        # REMOVE: Legacy CLI integration
│   ├── session.py            # Modified: Enhanced for bidirectional
│   ├── facade.py             # Modified: Route to new agent_integration
│   └── ...
├── security/                 # Existing - unchanged
├── storage/                  # Existing - unchanged
├── config/                   # Modified - new SDK options
│   └── settings.py           # Add ClaudeAgentOptions fields
└── main.py                   # Modified - initialization changes

tests/
├── test_claude/
│   ├── test_agent_integration.py  # NEW
│   ├── test_tools.py              # NEW
│   ├── test_hooks.py              # NEW
│   ├── test_commands.py           # NEW
│   └── ...
└── ...
```

**Structure Decision**: Extends existing single-project structure. New modules added under `src/claude/` for tools, hooks, and commands. Removed legacy SDK integration files replaced with new agent integration.

## Complexity Tracking

> No constitution violations. All changes align with existing architecture.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | - | - |
