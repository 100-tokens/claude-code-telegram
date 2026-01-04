# cc-telegram Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-04

## Active Technologies
- Python 3.10+ (upgraded from 3.9, breaking change accepted per clarification) + claude-agent-sdk (0.1.17+), python-telegram-bot, aiosqlite, structlog (002-agent-sdk-upgrade)
- SQLite via aiosqlite (existing schema compatible) (002-agent-sdk-upgrade)
- Python 3.10+ + python-telegram-bot, structlog, pydantic-settings, click (new, for enhanced CLI) (003-cli-bot-launcher)
- SQLite via aiosqlite (existing) (003-cli-bot-launcher)

- Markdown (documentation only) + None (documentation update) (001-docs-update)

## Project Structure

```text
src/
tests/
```

## Commands

# Add commands for Markdown (documentation only)

## Code Style

Markdown (documentation only): Follow standard conventions

## Recent Changes
- 003-cli-bot-launcher: Added Python 3.10+ + python-telegram-bot, structlog, pydantic-settings, click (new, for enhanced CLI)
- 002-agent-sdk-upgrade: Added Python 3.10+ (upgraded from 3.9, breaking change accepted per clarification) + claude-agent-sdk (0.1.17+), python-telegram-bot, aiosqlite, structlog

- 001-docs-update: Added Markdown (documentation only) + None (documentation update)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
