# Research: Claude Agent SDK Upgrade

**Feature**: 002-agent-sdk-upgrade
**Date**: 2025-01-04
**Status**: Complete

## Research Summary

This document consolidates research findings for migrating from `claude-code-sdk` to `claude-agent-sdk`. All technical decisions are resolved and ready for implementation.

---

## Topic 1: Claude Agent SDK Migration Path

### Decision
Use `claude-agent-sdk` version 0.1.17+ with clean cutover (no backward compatibility layer).

### Rationale
- The new SDK provides bundled CLI, eliminating external dependency
- In-process MCP tools offer better performance than subprocess-based tools
- `ClaudeAgentOptions` consolidates configuration previously spread across multiple parameters
- Hook system enables fine-grained permission control not possible with old SDK

### Key API Changes

| Old SDK (`claude-code-sdk`) | New SDK (`claude-agent-sdk`) |
|----------------------------|------------------------------|
| `ClaudeCodeOptions` | `ClaudeAgentOptions` |
| `query()` only | `query()` + `ClaudeSDKClient` |
| External MCP servers | In-process + external MCP servers |
| No hooks | `PreToolUse` hooks with `HookMatcher` |
| Separate CLI install | Bundled CLI |

### Migration Steps
1. Update `pyproject.toml`: Replace `claude-code-sdk = "^0.0.11"` with `claude-agent-sdk = "^0.1.17"`
2. Update imports: `from claude_agent_sdk import ...`
3. Replace `ClaudeCodeOptions` with `ClaudeAgentOptions`
4. Update error handling for new exception types
5. Remove CLI path detection logic (bundled CLI auto-detected)

### Alternatives Considered
- **Gradual migration with feature flags**: Rejected - adds complexity, dual maintenance burden
- **Fork old SDK**: Rejected - no ongoing maintenance, missing new features

---

## Topic 2: In-Process MCP Tools for Telegram

### Decision
Implement four Telegram-specific tools using `@tool` decorator and `create_sdk_mcp_server`:
1. `telegram_keyboard` - Send inline keyboard buttons
2. `telegram_file` - Send file attachments
3. `telegram_progress` - Update progress messages
4. `telegram_message` - Send formatted messages

### Rationale
- In-process tools run without subprocess overhead
- Direct access to Telegram bot context enables rich interactions
- Claude can decide when to use these tools based on context

### Implementation Pattern

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("telegram_keyboard", "Display inline keyboard to user", {
    "buttons": list,  # List of button labels
    "message": str    # Message to display with keyboard
})
async def telegram_keyboard(args):
    # Access bot context via closure or global
    keyboard = create_inline_keyboard(args["buttons"])
    await send_message(args["message"], reply_markup=keyboard)
    return {"content": [{"type": "text", "text": "Keyboard sent"}]}
```

### Tool Registration

```python
telegram_server = create_sdk_mcp_server(
    name="telegram",
    version="1.0.0",
    tools=[telegram_keyboard, telegram_file, telegram_progress, telegram_message]
)

options = ClaudeAgentOptions(
    mcp_servers={"telegram": telegram_server},
    allowed_tools=["mcp__telegram__keyboard", "mcp__telegram__file", ...]
)
```

### Alternatives Considered
- **External MCP server**: Rejected - subprocess overhead, complex IPC
- **Post-processing response**: Rejected - Claude can't request rich output

---

## Topic 3: Slash Command Expansion

### Decision
Discover and expand slash commands from `.claude/commands/` directory at bot startup. Intercept messages starting with `/speckit.` or `/ralph-` patterns and expand using template content.

### Rationale
- Enables Claude Code workflows from Telegram
- Templates already exist in project from spec-kit installation
- No modification to template files needed

### Implementation Pattern

```python
class SlashCommandLoader:
    def __init__(self, commands_dir: Path):
        self.commands = {}
        self._discover_commands(commands_dir)

    def _discover_commands(self, dir: Path):
        for md_file in dir.glob("*.md"):
            name = md_file.stem  # e.g., "speckit.specify"
            self.commands[name] = md_file.read_text()

    def expand(self, command: str, args: str) -> str:
        template = self.commands.get(command)
        if not template:
            raise UnknownCommandError(command)
        return template.replace("$ARGUMENTS", args)
```

### Command Matching
- `/speckit.specify "description"` → Load `speckit.specify.md`, expand with description
- `/ralph-loop "prompt"` → Load `ralph-loop.md`, expand with prompt
- Unknown commands → Return error with available command list

### Alternatives Considered
- **Hardcoded command handlers**: Rejected - not extensible, duplicate logic
- **Dynamic command generation**: Rejected - templates already provide structure

---

## Topic 4: PreToolUse Hooks for Security

### Decision
Implement security hooks using SDK's `PreToolUse` hook system with `HookMatcher` for pattern-based tool filtering.

### Rationale
- Adds defense layer beyond tool whitelist
- Can block specific dangerous patterns (e.g., `rm -rf`)
- Supports user confirmation flows for sensitive operations
- Integrates with existing audit logging

### Implementation Pattern

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r">\s*/dev/",
    r"chmod\s+777",
    r"git\s+push\s+--force",
]

async def security_hook(input_data, tool_use_id, context):
    if input_data["tool_name"] != "Bash":
        return {}

    command = input_data["tool_input"].get("command", "")

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            audit_log.warning("Blocked dangerous command", command=command)
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked: matches dangerous pattern"
                }
            }
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[security_hook])
        ]
    }
)
```

### Hook Categories
1. **Block hooks**: Deny dangerous operations outright
2. **Confirm hooks**: Request user approval via Telegram callback
3. **Audit hooks**: Log all tool usage for review

### Alternatives Considered
- **Tool whitelist only**: Rejected - too coarse, can't filter by arguments
- **Post-execution validation**: Rejected - damage already done

---

## Topic 5: ClaudeSDKClient for Bidirectional Sessions

### Decision
Use `ClaudeSDKClient` as async context manager for stateful, bidirectional conversations instead of one-shot `query()` calls.

### Rationale
- Maintains conversation state across multiple exchanges
- Supports interruption via client close
- Better session isolation per user
- Enables future features like conversation forking

### Implementation Pattern

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

class ConversationManager:
    def __init__(self):
        self.clients: Dict[int, ClaudeSDKClient] = {}

    async def get_client(self, user_id: int, options: ClaudeAgentOptions) -> ClaudeSDKClient:
        if user_id not in self.clients:
            client = ClaudeSDKClient(options=options)
            await client.__aenter__()
            self.clients[user_id] = client
        return self.clients[user_id]

    async def send_message(self, user_id: int, prompt: str):
        client = await self.get_client(user_id, self.options)
        await client.query(prompt)
        async for msg in client.receive_response():
            yield msg

    async def close_session(self, user_id: int):
        if user_id in self.clients:
            await self.clients[user_id].__aexit__(None, None, None)
            del self.clients[user_id]
```

### Session Lifecycle
1. First message: Create `ClaudeSDKClient`, enter context
2. Subsequent messages: Reuse existing client
3. Timeout/explicit close: Exit context, cleanup
4. Interruption: Close client mid-response

### Alternatives Considered
- **Continue using `query()`**: Rejected - no state, no interruption
- **External session storage**: Rejected - SDK handles session internally

---

## Topic 6: Python 3.10+ Compatibility

### Decision
Bump minimum Python version to 3.10+ in `pyproject.toml`.

### Rationale
- Claude Agent SDK requires Python 3.10+
- Enables use of modern syntax (match statements, type unions with `|`)
- Most deployment environments already support 3.10+

### Migration Steps
1. Update `pyproject.toml`: `python = "^3.10"`
2. Update CI/CD workflows to use Python 3.10+
3. Update Dockerfile base image
4. Document breaking change in release notes

### Breaking Change Mitigation
- Clear documentation in README about version requirement
- CHANGELOG entry explaining migration
- No gradual deprecation (clean cutover per clarification)

---

## Conclusion

All technical decisions are resolved. The migration path is clear:

1. **Dependencies**: Replace SDK, bump Python version
2. **Integration**: New `agent_integration.py` with `ClaudeSDKClient`
3. **Tools**: Four Telegram tools via in-process MCP server
4. **Commands**: Loader for `.claude/commands/` templates
5. **Hooks**: Security hooks for dangerous pattern blocking
6. **Session**: `ConversationManager` for per-user clients

**Next Phase**: Phase 1 - Design artifacts (quickstart.md)
