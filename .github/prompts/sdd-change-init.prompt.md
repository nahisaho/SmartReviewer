# MUSUBIX Change Init Command

Initialize a change proposal for brownfield projects (existing codebase).

---

## Instructions for AI Agent

You are executing the `musubix change init [change-name]` command to create a change proposal for an existing codebase.

### Command Format

```bash
npx musubix change init add-2fa
npx musubix change init migrate-to-graphql
npx musubix change init refactor-auth-service
```

### Your Task

Generate a change proposal specification that documents what will be added, modified, or removed in the existing MUSUBIX system.

---

## Process

### 1. Read Steering Context (Article VI)

**IMPORTANT**: Before starting, read steering files:

```bash
steering/product.ja.md      # Current product context
steering/structure.ja.md    # Existing architecture
steering/tech.ja.md         # Current technology stack
```

---

### 2. Analyze Existing System

**Research Current Implementation**:

```bash
# Search for related code
grep -r "{{related-feature}}" packages/

# Find existing requirements
ls storage/specs/REQ-*.md

# Check existing design documents
ls storage/specs/DES-*.md
```

**Document Current State**:

- What exists now?
- What packages are affected?
- What dependencies exist?
- What tests cover this area?

---

### 3. Gather Change Requirements

**Ask User**:

- Why is this change needed?
- What problem does it solve?
- What must NOT change (backward compatibility)?
- What is the timeline?

**Impact Analysis**:

- [ ] packages/core/ components
- [ ] packages/mcp-server/ tools
- [ ] packages/yata-client/ integration
- [ ] CLI commands
- [ ] Tests
- [ ] Documentation

---

### 4. Generate Change Proposal

**Output**: `storage/changes/{{CHANGE_NAME}}-proposal.md`

```markdown
# Change Proposal: {{CHANGE_NAME}}

**Document ID**: CHG-{{CHANGE}}-001
**Version**: 1.0.0
**Date**: {{DATE}}
**Status**: Proposed

## Summary

**Change Type**: Feature / Enhancement / Refactor / Bug Fix
**Affected Packages**: packages/core/, packages/mcp-server/
**Risk Level**: Low / Medium / High

## Motivation

**Problem Statement**:
[Why is this change needed?]

**Business Value**:
[What value does this provide?]

## Current State

### Existing Implementation

| Component | Location | Description |
|-----------|----------|-------------|
| AuthService | packages/core/src/auth/ | Current auth implementation |

### Existing Tests

| Test File | Coverage |
|-----------|----------|
| auth.test.ts | 85% |

## Proposed Changes

### ADDED Requirements

#### REQ-{{COMPONENT}}-NEW-001: [New Feature]

> [EARS statement]

**Priority**: P1
**Acceptance Criteria**:
- [ ] [Criterion 1]

### MODIFIED Requirements

#### REQ-{{COMPONENT}}-001: [Modified Feature]

**Current**:
> [Current EARS statement]

**Proposed**:
> [New EARS statement]

**Change Reason**: [Why modify?]

### REMOVED Requirements

#### REQ-{{COMPONENT}}-OLD-001: [Deprecated Feature]

**Reason**: [Why remove?]
**Migration Path**: [How to migrate?]

## Impact Analysis

### Affected Components

| Package | Component | Impact |
|---------|-----------|--------|
| core | auth/service.ts | Modified |
| mcp-server | tools/auth-tools.ts | Modified |

### Breaking Changes

- [ ] CLI API changes
- [ ] MCP tool changes
- [ ] Type changes

### Migration Requirements

1. [Migration step 1]
2. [Migration step 2]

## Implementation Plan

### Phase 1: Preparation

- [ ] Create feature branch
- [ ] Write tests for new requirements
- [ ] Update documentation

### Phase 2: Implementation

- [ ] Implement changes
- [ ] Update affected components
- [ ] Add feature flag (if needed)

### Phase 3: Validation

- [ ] Run all tests
- [ ] Validate traceability
- [ ] Code review

## Rollback Plan

1. Revert feature flag
2. Deploy previous version
3. Restore database (if needed)

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Architect | | | Pending |
| Lead Dev | | | Pending |
```

---

### 5. Delta Specification

For modifications, create delta spec:

```markdown
## Delta Specification

### packages/core/src/auth/service.ts

**Change Type**: Modified

**Current Implementation**:
\`\`\`typescript
export class AuthService {
  async login(email: string, password: string): Promise<Session> {
    // Current implementation
  }
}
\`\`\`

**Proposed Implementation**:
\`\`\`typescript
export class AuthService {
  async login(email: string, password: string, mfaCode?: string): Promise<Session> {
    // New implementation with MFA support
    if (this.config.mfaEnabled && !mfaCode) {
      throw new MFARequiredError();
    }
  }
}
\`\`\`

**Breaking Change**: Yes - New optional parameter
**Migration**: Update all callers to handle MFARequiredError
```

---

### 6. Traceability

Link to existing documents:

```markdown
## Traceability

### Related Requirements
- REQ-AUTH-001: User authentication (MODIFIED)
- REQ-AUTH-NEW-001: MFA support (ADDED)

### Related Design
- DES-AUTH-001: Authentication design (UPDATE REQUIRED)

### Related Tasks
- TSK-AUTH-001: Implement MFA (NEW)
```

---

**MUSUBIX**: https://github.com/nahisaho/MUSUBIX
**Version**: 1.0.0
