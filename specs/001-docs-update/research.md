# Research: Documentation Update with Development Tooling

**Feature**: 001-docs-update
**Date**: 2025-01-04
**Status**: Complete

## Research Summary

This documentation update requires no external research as all tools are already installed and verified. This document consolidates the existing tool configurations for reference during implementation.

---

## Tool 1: Spec-kit

### Decision
Use spec-kit for spec-driven development workflow with Claude Code integration.

### Rationale
- Already installed via `uv tool install specify-cli`
- Provides structured workflow: specify → plan → tasks → implement
- Integrates with Claude Code slash commands

### Available Commands
| Command | Description |
|---------|-------------|
| `/speckit.specify` | Create feature specification from description |
| `/speckit.clarify` | Ask clarification questions for underspecified areas |
| `/speckit.plan` | Generate implementation plan from spec |
| `/speckit.tasks` | Generate actionable task breakdown |
| `/speckit.implement` | Execute implementation tasks |
| `/speckit.analyze` | Cross-artifact consistency analysis |
| `/speckit.checklist` | Generate custom checklists |
| `/speckit.constitution` | Create/update project constitution |

### Alternatives Considered
- Manual specification writing: Rejected - no structured workflow
- Other spec tools: Not evaluated - spec-kit already installed

---

## Tool 2: Ralph-wiggum

### Decision
Use ralph-wiggum for iterative AI-assisted development loops.

### Rationale
- Claude Code plugin for continuous improvement cycles
- Useful for complex tasks requiring multiple iterations
- Stop hook provides iteration control

### Available Commands
| Command | Description |
|---------|-------------|
| `/ralph-loop "<prompt>" --max-iterations N` | Start iterative loop |
| `/cancel-ralph` | Cancel active loop |
| `/help` | Plugin help |

### Configuration
- Location: `.claude/plugins/ralph-wiggum/`
- Hooks: Stop hook intercepts exits to continue iterations
- Completion: Output `<promise>COMPLETE</promise>` to exit loop

### Alternatives Considered
- Manual iteration: Rejected - no automatic continuation
- Other iteration tools: Not available for Claude Code

---

## Tool 3: PR-Agent

### Decision
Use PR-Agent with Gemini 3 Flash via OpenRouter for automated PR reviews.

### Rationale
- GitHub Action for automated PR analysis
- Security-focused reviews align with constitution
- Auto-review, auto-describe, auto-improve enabled

### Configuration
| Setting | Value |
|---------|-------|
| Model | `openrouter/google/gemini-3-flash-preview` |
| Fallback | `openrouter/google/gemini-2.0-flash-001` |
| Auto Review | Enabled |
| Auto Describe | Enabled |
| Security Review | Enabled |
| Test Review | Enabled |

### PR Commands
| Command | Description |
|---------|-------------|
| `/review` | Request AI code review |
| `/describe` | Generate PR description |
| `/improve` | Get code improvement suggestions |
| `/ask <question>` | Ask about the PR |

### Alternatives Considered
- GitHub Copilot: Not installed, different focus
- Manual reviews only: Less thorough, slower

---

## Tool 4: Project Constitution

### Decision
Reference constitution at `.specify/memory/constitution.md` in README.

### Rationale
- Establishes project governance and principles
- Guides contributor expectations
- Version 1.0.0 ratified 2025-01-04

### Core Principles Summary
1. **Security-First Design**: Defense-in-depth, authentication, sandboxing
2. **Async-First Architecture**: Non-blocking I/O, aiosqlite, async handlers
3. **Clean Separation of Concerns**: Layered architecture (bot/claude/security/storage)
4. **Test-First Development**: 80%+ coverage for security modules
5. **User Experience Focus**: Clear errors, progress indicators, familiar commands
6. **Defensive Cost Management**: Per-user limits, session timeouts, cost tracking

---

## README Section Placement Research

### Current README Structure Analysis
1. Title and badges
2. What is this?
3. Quick Start / Demo
4. Features (Working, New, Planned)
5. Claude AI Integration
6. Terminal-like Interface
7. Enterprise-Grade Security
8. Developer Experience
9. Installation
10. Usage
11. Configuration
12. Troubleshooting
13. Security
14. Contributing
15. License

### Recommended New Section Placement

**Option A (Recommended)**: Add "AI-Assisted Development" section after "Contributing" (before License)
- Keeps user-focused sections together at top
- Groups developer tooling near contribution guidelines

**Option B**: Add within "Contributing" section as subsection
- Tighter coupling with contribution workflow
- May make Contributing section too long

**Decision**: Option A - New standalone section "AI-Assisted Development" after Contributing

---

## Feature Status Verification Research

### Features to Verify
Based on security audit performed earlier, all listed "Working Features" have corresponding implementations:

| Feature | Implementation Location | Status |
|---------|------------------------|--------|
| Telegram bot functionality | `src/bot/core.py` | Verified |
| Directory navigation | `src/bot/handlers/` | Verified |
| Multi-layer auth | `src/security/auth.py` | Verified |
| Rate limiting | `src/security/rate_limiter.py` | Verified |
| Claude integration | `src/claude/` | Verified |
| File upload | `src/bot/handlers/` | Verified |
| Git integration | `src/bot/features/git_integration.py` | Verified |
| Quick actions | `src/bot/` | Verified |
| Session export | Documented | Verify during impl |
| SQLite persistence | `src/storage/database.py` | Verified |
| Audit logging | `src/security/audit.py` | Verified |

### Planned Features Status
All items in "Planned Enhancements" confirmed not yet implemented per security audit.

---

## Conclusion

No external research needed. All tools are installed and configured. Research consolidates existing configurations for documentation reference.

**Next Phase**: Phase 1 - Design artifacts (data-model.md, contracts/, quickstart.md)
