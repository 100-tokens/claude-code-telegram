# Quickstart: CLI Bot Launcher

**Feature**: 003-cli-bot-launcher
**Date**: 2026-01-04

## Prerequisites

1. Python 3.10 or higher
2. Poetry installed
3. Telegram bot token from @BotFather
4. Claude CLI authenticated (`claude --version` works)

## Installation

```bash
# Clone the repository
git clone https://github.com/100-tokens/claude-code-telegram.git
cd claude-code-telegram

# Install dependencies
poetry install
```

## Quick Start

### 1. Navigate to Your Project

```bash
cd /path/to/your/project
```

### 2. Create Configuration

Create a `.env` file with minimum required settings:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_token_from_botfather
TELEGRAM_BOT_USERNAME=your_bot_username

# Optional - defaults to current directory
# APPROVED_DIRECTORY=/path/to/directory
```

### 3. Start the Bot

```bash
# Start bot using current directory as approved directory
claude-telegram-bot

# Or specify a different directory
claude-telegram-bot --directory /path/to/project
```

### 4. Verify Startup

You should see:
```
╭─────────────────────────────────────────────────────────────╮
│  Claude Code Telegram Bot v0.1.0                            │
├─────────────────────────────────────────────────────────────┤
│  Bot:       @your_bot_username                              │
│  Directory: /path/to/your/project                           │
│  Features:  SDK, Git, Quick Actions                         │
│  Status:    Ready                                           │
╰─────────────────────────────────────────────────────────────╯
```

### 5. Test the Bot

1. Open Telegram
2. Search for your bot username
3. Send `/start`
4. Try a simple command: "What files are in this directory?"

## CLI Reference

```bash
# Show help
claude-telegram-bot --help

# Show version
claude-telegram-bot --version

# Start with debug logging
claude-telegram-bot --debug

# Start with specific directory
claude-telegram-bot --directory /path/to/project

# Start with config file
claude-telegram-bot --config-file /path/to/.env
```

## Common Issues

### Missing TELEGRAM_BOT_TOKEN

```
Error: Missing required configuration

  TELEGRAM_BOT_TOKEN is not set

To fix:
  1. Create a .env file in the current directory
  2. Add: TELEGRAM_BOT_TOKEN=your_token_here
```

**Solution**: Get a token from @BotFather on Telegram

### Directory Not Found

```
Error: Directory does not exist: /path/to/invalid
```

**Solution**: Verify the path exists and is accessible

### Permission Denied

```
Error: Cannot access directory: /path/to/protected
```

**Solution**: Check directory permissions (`ls -la /path/to/protected`)

## Graceful Shutdown

Press `Ctrl+C` to stop the bot:

```
Shutting down...
  Sessions closed: 2
  Cleanup complete
Goodbye!
```

## Development Mode

For development with verbose logging:

```bash
# Enable debug mode
claude-telegram-bot --debug

# With specific .env
claude-telegram-bot --debug --config-file .env.development
```

## Validation Checklist

- [ ] Bot starts without errors
- [ ] Startup banner shows correct directory
- [ ] Bot responds to `/start` command
- [ ] Bot can list files in approved directory
- [ ] Ctrl+C shuts down gracefully
- [ ] `--help` displays usage information
- [ ] `--version` shows version number
