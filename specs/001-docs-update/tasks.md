# Tasks: Documentation Update with Development Tooling

**Input**: Design documents from `/specs/001-docs-update/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, quickstart.md

**Tests**: No tests required for documentation-only feature.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Primary file**: `README.md` at repository root
- **Reference files**: `.specify/memory/constitution.md`, `.claude/commands/`, `.github/workflows/`

---

## Phase 1: Setup (Preparation)

**Purpose**: Review existing documentation and gather reference material

- [x] T001 Review current README.md structure and identify insertion points in README.md
- [x] T002 [P] Review constitution content at .specify/memory/constitution.md for principle summaries
- [x] T003 [P] Review spec-kit commands in .claude/commands/ for documentation reference
- [x] T004 [P] Review ralph-wiggum plugin at .claude/plugins/ralph-wiggum/ for usage documentation
- [x] T005 [P] Review PR-Agent configuration in .github/workflows/pr_agent.yml and .pr_agent.toml

---

## Phase 2: User Story 1 - Development Workflow Tools (Priority: P1)

**Goal**: Document spec-kit, ralph-wiggum, and PR-Agent in a new "AI-Assisted Development" section

**Independent Test**: A new developer can read the README and successfully understand how to use `/speckit.specify`, `/ralph-loop`, and PR comment commands

### Implementation for User Story 1

- [x] T006 [US1] Create "AI-Assisted Development" section header after "Contributing" section in README.md
- [x] T007 [US1] Write spec-kit subsection with command table and workflow overview in README.md
- [x] T008 [US1] Write ralph-wiggum subsection with usage example and when to use it in README.md
- [x] T009 [US1] Write PR-Agent subsection documenting auto-review features and PR commands in README.md
- [x] T010 [US1] Add links to detailed documentation for each tool in README.md

**Checkpoint**: User Story 1 complete - developers can find and understand development workflow tools

---

## Phase 3: User Story 2 - Project Governance (Priority: P2)

**Goal**: Add constitution reference with core principles summary

**Independent Test**: A contributor can read the governance section and correctly identify the 6 core principles

### Implementation for User Story 2

- [x] T011 [US2] Create "Project Constitution" subsection within AI-Assisted Development in README.md
- [x] T012 [US2] Add link to .specify/memory/constitution.md in README.md
- [x] T013 [US2] Write brief summaries of all 6 core principles in README.md
- [x] T014 [US2] Add governance version and amendment reference in README.md

**Checkpoint**: User Story 2 complete - contributors understand project principles and governance

---

## Phase 4: User Story 3 - Feature Status Accuracy (Priority: P3)

**Goal**: Verify and update feature status to match actual codebase

**Independent Test**: Cross-reference each documented feature with codebase to verify accuracy

### Implementation for User Story 3

- [x] T015 [US3] Cross-reference "Working Features" list with src/ implementations in README.md
- [x] T016 [US3] Verify "Planned Enhancements" are not yet implemented in README.md
- [x] T017 [US3] Update any inaccurate feature status labels in README.md
- [x] T018 [US3] Add note about new tooling (spec-kit, ralph-wiggum, PR-Agent) to Working Features if not present in README.md

**Checkpoint**: User Story 3 complete - all feature statuses accurately reflect codebase state

---

## Phase 5: Polish & Validation

**Purpose**: Final quality checks and consistency validation

- [x] T019 Verify markdown formatting and lint README.md
- [x] T020 [P] Ensure consistent emoji and heading style with existing README sections in README.md
- [x] T021 [P] Check all links resolve correctly (constitution, tool docs) in README.md
- [x] T022 Review complete section for readability and completeness in README.md
- [x] T023 Run quickstart.md validation checklist from specs/001-docs-update/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - gather reference material first
- **User Story 1 (Phase 2)**: Depends on Setup - creates the main section structure
- **User Story 2 (Phase 3)**: Can run after Setup, independent of US1
- **User Story 3 (Phase 4)**: Can run after Setup, independent of US1/US2
- **Polish (Phase 5)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - creates new section
- **User Story 2 (P2)**: Writes to section created by US1 - should follow US1
- **User Story 3 (P3)**: Independent - modifies existing features section

### Parallel Opportunities

- T002, T003, T004, T005 can all run in parallel (different reference files)
- T020, T021 can run in parallel (different validation aspects)
- US2 and US3 could theoretically run in parallel but edit same file (recommend sequential)

---

## Parallel Example: Setup Phase

```bash
# Launch all reference reviews together:
Task: "Review constitution content at .specify/memory/constitution.md"
Task: "Review spec-kit commands in .claude/commands/"
Task: "Review ralph-wiggum plugin at .claude/plugins/ralph-wiggum/"
Task: "Review PR-Agent configuration in .github/workflows/pr_agent.yml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (gather all references)
2. Complete Phase 2: User Story 1 (development tools documentation)
3. **STOP and VALIDATE**: Verify new section is readable and complete
4. Commit as working increment

### Incremental Delivery

1. Complete Setup → Reference material gathered
2. Add User Story 1 → Development tools documented → Commit
3. Add User Story 2 → Constitution reference added → Commit
4. Add User Story 3 → Feature status verified → Commit
5. Polish → Final quality check → Final commit

### Recommended Execution Order

Since all tasks edit README.md, sequential execution is recommended:
1. T001-T005 (Setup - parallel where marked)
2. T006-T010 (US1 - sequential, same file)
3. T011-T014 (US2 - sequential, same file)
4. T015-T018 (US3 - sequential, same file)
5. T019-T023 (Polish - parallel where marked)

---

## Notes

- All documentation tasks edit README.md - avoid parallel execution of different user stories
- [P] tasks within Setup phase can run in parallel (reading different files)
- Each user story checkpoint represents a committable state
- Verify markdown renders correctly on GitHub after each story
- Total: 23 tasks across 5 phases
