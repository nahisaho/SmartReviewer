# MUSUBIX Tasks Command

Break down design into actionable implementation tasks.

---

## Instructions for AI Agent

You are executing the `musubix tasks [feature-name]` command to create a task breakdown document.

### Command Format

```bash
npx musubix tasks generate design.md
```

### Your Task

Generate a comprehensive task breakdown that transforms the design into actionable implementation tasks with full requirements traceability.

---

## Process

### 1. Read Context

**CRITICAL**: Read these files first:

```bash
# Design and Requirements
storage/specs/DES-{{FEATURE}}-001.md
storage/specs/REQ-{{FEATURE}}-001.md

# Steering Context
steering/structure.ja.md
steering/tech.ja.md
steering/product.ja.md
```

---

### 2. Verify Prerequisites

**Check design file exists**:

```markdown
❌ **Error**: Design document not found

Expected: storage/specs/DES-{{FEATURE}}-001.md

Please run `npx musubix design generate` first.

Tasks cannot be created without design (Article V: Traceability).
```

---

### 3. Generate Task Breakdown

**Output**: `storage/specs/TSK-{{FEATURE}}-001.md`

#### Task Structure

```markdown
### TSK-{{FEATURE}}-NNN: [Task Title]

**Priority**: P0/P1/P2/P3
**Story Points**: 1/2/3/5/8/13
**Estimated Hours**: N
**Status**: Not Started

**Description**:
[Clear description]

**Requirements Coverage**:
- REQ-{{COMPONENT}}-NNN: [Requirement title]

**Package**: packages/core/ | packages/mcp-server/ | packages/yata-client/

**Files to Create/Modify**:
- `packages/core/src/{{feature}}/index.ts`
- `packages/core/__tests__/unit/{{feature}}.test.ts`

**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Test-First Checklist** (Article III):
- [ ] Tests written BEFORE implementation
- [ ] Red: Failing test committed
- [ ] Green: Minimal implementation passes
- [ ] Blue: Refactored with confidence

**Dependencies**:
- TSK-{{FEATURE}}-NNN: [Dependency]
```

---

### 4. Task Categories (MUSUBIX-specific)

**P0 Tasks (Critical)**:

1. **TSK-001: Set Up Package Structure**
   - Create in `packages/{{package}}/src/{{feature}}/`
   - Follow Article I (Library-First)

2. **TSK-002: Write Tests (RED)**
   - Location: `packages/{{package}}/__tests__/unit/{{feature}}.test.ts`
   - Test all acceptance criteria

3. **TSK-003: Implement Code (GREEN)**
   - Minimal implementation to pass tests
   - Location: `packages/{{package}}/src/{{feature}}/`

4. **TSK-004: Refactor (BLUE)**
   - Improve design while tests pass
   - Apply SOLID principles

5. **TSK-005: Add CLI Command (Article II)**
   - Location: `packages/core/src/cli/commands/{{feature}}.ts`
   - Register in `packages/core/src/cli/index.ts`

6. **TSK-006: Add MCP Tool (if needed)**
   - Location: `packages/mcp-server/src/tools/{{feature}}-tools.ts`
   - Register in `packages/mcp-server/src/server.ts`

**P1 Tasks (High)**:

7. **TSK-007: Integration Tests**
   - Location: `packages/{{package}}/__tests__/integration/`

8. **TSK-008: Documentation**
   - Update `docs/USER-GUIDE.md`
   - Update `docs/API-REFERENCE.md`

---

### 5. Test-First Mandate (Article III)

For EVERY implementation task, create 3 separate tasks:

```markdown
### TSK-002: Write Tests for REQ-{{COMPONENT}}-001 (RED) 🔴

**Priority**: P0
**Story Points**: 2

**Description**:
Write failing tests for requirement REQ-{{COMPONENT}}-001

**Test File**: `packages/core/__tests__/unit/{{feature}}.test.ts`

**Acceptance Criteria**:
- [ ] Tests compile successfully
- [ ] Tests FAIL (no implementation yet)
- [ ] Tests cover all acceptance criteria

---

### TSK-003: Implement REQ-{{COMPONENT}}-001 (GREEN) 💚

**Priority**: P0
**Story Points**: 3
**Depends On**: TSK-002

**Description**:
Implement minimal code to pass tests

**Acceptance Criteria**:
- [ ] All tests from TSK-002 pass
- [ ] No extra functionality added

---

### TSK-004: Refactor REQ-{{COMPONENT}}-001 (BLUE) 💙

**Priority**: P0
**Story Points**: 2
**Depends On**: TSK-003

**Description**:
Refactor while keeping tests green

**Acceptance Criteria**:
- [ ] All tests still pass
- [ ] SOLID principles applied
- [ ] Code quality improved
```

---

### 6. Task Document Template

```markdown
# Task Breakdown: {{FEATURE_NAME}}

**Document ID**: TSK-{{FEATURE}}-001
**Version**: 1.0.0
**Date**: {{DATE}}
**Design**: DES-{{FEATURE}}-001
**Requirements**: REQ-{{FEATURE}}-001

## Summary

| Priority | Count | Story Points |
|----------|-------|--------------|
| P0 | X | XX |
| P1 | X | XX |
| Total | X | XX |

## Sprint Plan

### Sprint 1 (Week 1)
- TSK-{{FEATURE}}-001: Setup
- TSK-{{FEATURE}}-002: Tests (RED)
- TSK-{{FEATURE}}-003: Implementation (GREEN)

### Sprint 2 (Week 2)
- TSK-{{FEATURE}}-004: Refactor (BLUE)
- TSK-{{FEATURE}}-005: CLI Command

## Task Details

### TSK-{{FEATURE}}-001: [Title]
...

## Traceability Matrix

| Task | Requirement | Design | Test |
|------|-------------|--------|------|
| TSK-001 | REQ-XXX-001 | DES-XXX-001 | xxx.test.ts |

## Definition of Done

- [ ] All tests pass
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Traceability verified
```

---

### 7. MCP Tool Integration

Use MUSUBIX MCP tools:

```
sdd_create_tasks - Generate tasks from design
```

---

**MUSUBIX**: https://github.com/nahisaho/MUSUBIX
**Version**: 1.0.0
