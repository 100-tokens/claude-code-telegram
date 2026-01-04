# Research: CLI Bot Launcher

**Feature**: 003-cli-bot-launcher
**Date**: 2026-01-04

## Research Topics

### R-001: CLI Framework Comparison

**Question**: Should we use `click`, `typer`, or stick with `argparse`?

**Findings**:

| Framework | Pros | Cons |
|-----------|------|------|
| argparse | Built-in, no deps | Verbose, limited formatting |
| click | Rich features, decorators, groups | Extra dependency |
| typer | Type hints, modern | Built on click, more deps |

**Decision**: Use `click`
**Rationale**:
- Already a common pattern in Python CLIs
- Supports command groups for future expansion (`cc-telegram start`, `cc-telegram config`)
- Excellent help text formatting
- Minimal footprint (single dependency)

### R-002: Current Directory as Approved Directory

**Question**: How to safely use CWD as the approved directory?

**Findings**:
- `Path.cwd()` returns absolute path, cross-platform
- Must validate directory exists and is readable
- Should resolve symlinks for security
- Need to handle permission errors gracefully

**Decision**: Use `Path.cwd().resolve()` with validation
**Rationale**: Absolute resolved path prevents symlink attacks and provides consistent behavior

### R-003: Configuration Override Strategy

**Question**: How to override config from CLI without modifying `.env`?

**Findings**:
- pydantic-settings supports environment variable overrides
- Can set `APPROVED_DIRECTORY` via `os.environ` before loading config
- Click options can provide default values from env vars

**Decision**: Set environment variable before config load
**Rationale**:
- Cleanest integration with existing config system
- No changes to Settings class needed
- Works with validation already in place

### R-004: Startup Banner Design

**Question**: What information should be displayed on startup?

**Findings**:
- Users need confirmation bot started correctly
- Key info: bot username, approved directory, features enabled
- Should be concise but informative
- Color helps distinguish status from logs

**Decision**: Display structured banner with key configuration
**Rationale**: Immediate feedback helps users verify correct setup

**Example Banner**:
```
╭─────────────────────────────────────────────────────────────╮
│  Claude Code Telegram Bot v0.1.0                            │
├─────────────────────────────────────────────────────────────┤
│  Bot:       @heartbit1_bot                                  │
│  Directory: /Volumes/Pascal4Tb/Projects/myproject           │
│  Features:  SDK, Git, Quick Actions                         │
│  Status:    Ready                                           │
╰─────────────────────────────────────────────────────────────╯
```

### R-005: Graceful Shutdown Messaging

**Question**: What should be displayed on Ctrl+C?

**Findings**:
- Current implementation logs shutdown events
- Users want confirmation shutdown completed
- Should show cleanup stats (sessions closed, etc.)

**Decision**: Display shutdown confirmation with stats
**Rationale**: Confirms clean exit, useful for debugging

### R-006: Error Message Guidelines

**Question**: How to format configuration errors?

**Findings**:
- Current errors are technical (pydantic validation)
- Users need actionable guidance
- Should suggest specific fix

**Decision**: Wrap configuration errors with user-friendly messages

**Example**:
```
Error: Missing required configuration

  TELEGRAM_BOT_TOKEN is not set

To fix:
  1. Create a .env file in the current directory
  2. Add: TELEGRAM_BOT_TOKEN=your_token_here

Get a token from @BotFather on Telegram
```

## Alternatives Considered

### A-001: Use typer instead of click

**Rejected because**:
- Adds complexity (typer wraps click)
- Type hints for CLI aren't essential here
- Click is sufficient and more widely used

### A-002: Create separate binary for CWD mode

**Rejected because**:
- Duplicates code
- Confuses users with multiple entry points
- Single CLI with flag is cleaner

### A-003: Auto-detect .env location by walking up directories

**Rejected because**:
- Unpredictable behavior
- Could pick wrong project's config
- Explicit CWD is clearer

## Implementation Notes

1. **Backward Compatibility**: Keep existing `--config-file` flag working
2. **Poetry Script**: Keep `claude-telegram-bot` entry point
3. **Testing**: Mock `Path.cwd()` for unit tests
4. **Documentation**: Update README with new CLI usage
