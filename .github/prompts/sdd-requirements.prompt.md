# MUSUBIX Requirements Command

Create EARS-format requirements specification through interactive dialogue.

---

## Instructions for AI Agent

You are executing the `musubix requirements [feature-name]` command to create a requirements specification.

### Command Format

```bash
npx musubix requirements analyze authentication
npx musubix requirements validate spec.md
npx musubix requirements map spec.md
```

### Your Task

**CRITICAL**: Before generating requirements, engage in an interactive 1-on-1 dialogue with the user to uncover the TRUE PURPOSE behind their request.

### Output Directory

**Requirements documents are saved to**: `storage/specs/`

- File: `storage/specs/REQ-{{FEATURE}}-001.md`

---

## Process

### 1. Read Steering Context (Article VI)

**IMPORTANT**: Before starting, read steering files to understand project context:

```bash
# Read these files first
steering/product.ja.md      # Business context, users, goals
steering/structure.ja.md    # Architecture patterns
steering/tech.ja.md         # Technology stack
```

**Extract**:

- Target users
- Product goals
- Existing architecture patterns
- Technology constraints (TypeScript, Node.js 20+)

---

### 2. Interactive True Purpose Discovery

**CRITICAL RULE**: Ask ONE question at a time, then STOP and WAIT.

#### Question Sequence

**Turn 1**: WHY question
```
この機能で解決したい『本当の課題』は何ですか？
```

**Turn 2**: WHO question
```
この機能を最も必要としているのは誰ですか？
```

**Turn 3**: WHAT-IF question
```
もしこの機能が完璧に動作したら、何が変わりますか？
```

**Turn 4**: CONSTRAINT question
```
この機能で『絶対にやってはいけないこと』はありますか？
```

**Turn 5**: SUCCESS CRITERIA question
```
この機能が『成功した』と言えるのはどんな状態ですか？
```

---

### 3. Apply EARS Format (Article IV)

**CRITICAL**: All requirements MUST use one of 5 EARS patterns.

| Pattern | Syntax | Usage |
|---------|--------|-------|
| **Ubiquitous** | `The [system] SHALL [action]` | Always-active features |
| **Event-driven** | `WHEN [event], the [system] SHALL [action]` | User action triggers |
| **State-driven** | `WHILE [state], the [system] SHALL [action]` | Continuous conditions |
| **Unwanted** | `IF [error], THEN the [system] SHALL [action]` | Error handling |
| **Optional** | `WHERE [feature], the [system] SHALL [action]` | Feature flags |

---

### 4. Generate Requirements Document

**Template**:

```markdown
# Requirements Specification: {{FEATURE_NAME}}

**Document ID**: REQ-{{FEATURE}}-001
**Version**: 1.0.0
**Date**: {{DATE}}
**Status**: Draft

## Overview

- **Purpose**: [True purpose discovered through dialogue]
- **Scope**: [In/Out scope]
- **Package**: packages/core/ or packages/mcp-server/ or packages/yata-client/

## Stakeholders

| Role | Description | Needs |
|------|-------------|-------|
| Developer | Uses MUSUBIX CLI | Efficient workflow |

## Functional Requirements

### REQ-{{COMPONENT}}-001: [Title]

**EARS Pattern**: [Pattern name]

> [EARS statement]

**Priority**: P0/P1/P2/P3
**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Traceability**: → DES-{{FEATURE}}-001

## Non-Functional Requirements

### REQ-PERF-001: Performance
The system SHALL respond within 200ms for 95% of requests.

### REQ-SEC-001: Security
The system SHALL prevent OWASP Top 10 vulnerabilities.

## Traceability Matrix

| Requirement | Design | Task | Test |
|-------------|--------|------|------|
| REQ-{{COMPONENT}}-001 | DES-{{FEATURE}}-001 | TSK-{{FEATURE}}-001 | TBD |
```

---

### 5. Requirements ID Format

**Format**: `REQ-[COMPONENT]-[NUMBER]`

**Examples**:
- `REQ-CLI-001` - CLI component
- `REQ-MCP-001` - MCP Server component
- `REQ-YATA-001` - YATA Client component
- `REQ-CORE-001` - Core library component

---

### 6. Quality Checklist

Each requirement MUST have:

- [ ] Unique ID (REQ-COMPONENT-NNN)
- [ ] EARS pattern (one of 5)
- [ ] Clear SHALL statement
- [ ] Testable acceptance criteria
- [ ] Priority (P0/P1/P2/P3)
- [ ] Status (Draft initially)

---

### 7. MCP Tool Integration

Use MUSUBIX MCP tools:

```
sdd_create_requirements - Create requirements document
sdd_validate_requirements - Validate EARS patterns
```

---

**MUSUBIX**: https://github.com/nahisaho/MUSUBIX
**Version**: 1.0.0
