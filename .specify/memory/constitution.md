<!--
  SYNC IMPACT REPORT
  ==================
  Version Change: 0.0.0 → 1.0.0 (MAJOR - initial constitution)

  Modified Principles: N/A (initial creation)

  Added Sections:
  - Core Principles (6 principles)
  - Security Requirements
  - Development Workflow
  - Governance

  Removed Sections: N/A

  Templates Requiring Updates:
  - .specify/templates/plan-template.md: ✅ Compatible (Constitution Check section exists)
  - .specify/templates/tasks-template.md: ✅ Compatible (test-first pattern documented)

  Follow-up TODOs: None
-->

# Claude Code Telegram Bot Constitution

## Core Principles

### I. Security-First Design

All features MUST implement defense-in-depth security:
- Multi-layer authentication (whitelist + optional token-based) is REQUIRED for user access
- Directory sandboxing to `APPROVED_DIRECTORY` is NON-NEGOTIABLE; no file access outside this boundary
- Rate limiting with token bucket algorithm MUST be applied to all user-facing operations
- Input validation MUST protect against injection attacks, path traversal, and malicious payloads
- Audit logging MUST capture all security-relevant events for forensic analysis

**Rationale**: This bot provides remote code execution capabilities. A single security flaw could expose user systems to unauthorized access or data exfiltration.

### II. Async-First Architecture

All I/O operations MUST use async/await patterns:
- Database operations via `aiosqlite` - no blocking SQLite calls
- Network operations via `aiohttp` or async Telegram handlers
- File operations via `aiofiles` where applicable
- Claude SDK integration MUST use async streaming when available

**Rationale**: Telegram bots serve concurrent users. Blocking I/O would serialize requests and degrade user experience under load.

### III. Clean Separation of Concerns

Code MUST follow layered architecture:
- `src/bot/` - Telegram handlers and middleware (presentation layer)
- `src/claude/` - Claude integration logic (integration layer)
- `src/security/` - Authentication, validation, rate limiting (cross-cutting)
- `src/storage/` - Database and persistence (data layer)
- `src/config/` - Configuration management (infrastructure)

Features MUST NOT bypass layers; handlers MUST NOT access database directly without going through appropriate services.

**Rationale**: Clear boundaries enable independent testing, reduce coupling, and make the codebase navigable for contributors.

### IV. Test-First Development

For new features and bug fixes:
- Unit tests MUST exist for security-critical code (auth, validators, rate limiting)
- Integration tests SHOULD cover Claude SDK interactions and Telegram handler flows
- Test coverage MUST remain above 80% for `src/security/` modules
- Tests MUST run via `pytest` with async support (`pytest-asyncio`)

Red-Green-Refactor cycle is RECOMMENDED but not enforced for non-security code.

**Rationale**: Security code failures have outsized impact. High test coverage for security modules provides confidence against regressions.

### V. User Experience Focus

The bot MUST provide clear, actionable feedback:
- Error messages MUST explain what went wrong and suggest remediation
- Progress indicators MUST be shown for long-running operations
- Commands MUST follow familiar terminal patterns (`/cd`, `/ls`, `/pwd`)
- Quick actions MUST provide context-aware shortcuts for common tasks

**Rationale**: Users interact via mobile Telegram. Cryptic errors or silent failures make the bot unusable.

### VI. Defensive Cost Management

Resource consumption MUST be bounded:
- `CLAUDE_MAX_COST_PER_USER` MUST be enforced per user
- Session timeouts MUST expire idle sessions to free resources
- Request rate limits MUST prevent abuse and runaway costs
- Cost tracking MUST be logged for billing transparency

**Rationale**: Claude API calls incur real costs. Unbounded usage could result in unexpected charges for bot operators.

## Security Requirements

### Mandatory Security Controls

| Control | Implementation | Enforcement |
|---------|----------------|-------------|
| User Authentication | Whitelist or Token-based | Middleware blocks unauthenticated requests |
| Directory Isolation | Path validation in all file operations | SecurityValidator class |
| Rate Limiting | Token bucket per user | RateLimiter middleware |
| Input Sanitization | Command injection pattern detection | SecurityValidator class |
| Audit Logging | All auth attempts, file access, violations | AuditLogger class |

### Prohibited Actions

The following MUST NOT be implemented:
- Arbitrary command execution outside Claude sandbox
- Direct system file access (`/etc`, `/var`, `/proc`)
- Credential storage in plaintext
- Disabled security middleware in production
- Git operations that modify remote repositories without explicit user action

## Development Workflow

### Code Quality Gates

All PRs MUST pass:
1. `make lint` - Black, isort, flake8, mypy checks
2. `make test` - pytest with coverage report
3. Security review for any changes to `src/security/`

### Commit Standards

- Conventional commits format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `security`
- Security-related commits MUST use `security` type

### Branching Strategy

- `main` - stable, production-ready
- `feature/*` - new features
- `fix/*` - bug fixes
- `security/*` - security patches (prioritized review)

## Governance

### Amendment Process

1. Propose change via PR modifying this constitution
2. Document rationale and migration impact
3. Update dependent templates if principles change
4. Increment version per semantic versioning rules below

### Versioning Policy

- **MAJOR**: Principle removal, redefinition, or backward-incompatible governance change
- **MINOR**: New principle added, section materially expanded
- **PATCH**: Clarifications, typo fixes, non-semantic refinements

### Compliance Review

- All PRs MUST verify compliance with Core Principles
- Security PRs require sign-off from designated security reviewer (or bot owner)
- Constitution violations MUST be documented in Complexity Tracking if justified

**Version**: 1.0.0 | **Ratified**: 2025-01-04 | **Last Amended**: 2025-01-04
