# MUSUBIX Change Apply Command

Apply a change proposal to the codebase.

---

## Instructions for AI Agent

You are executing the `musubix change apply [change-name]` command to implement an approved change proposal.

### Command Format

```bash
npx musubix change apply add-2fa
npx musubix change apply migrate-to-graphql
```

### Your Task

Implement the changes defined in the change proposal, following constitutional governance.

---

## Process

### 1. Read Change Proposal

**IMPORTANT**: Read the approved change proposal first:

```bash
storage/changes/{{CHANGE_NAME}}-proposal.md
```

**Extract**:

- ADDED requirements
- MODIFIED requirements
- REMOVED requirements
- Implementation plan

**Verify Approval**:

- Status must be "Approved" (not "Proposed")
- If not approved, abort and notify user

---

### 2. Read Steering Context (Article VI)

```bash
steering/product.ja.md
steering/structure.ja.md
steering/tech.ja.md
```

---

### 3. Execute Implementation Plan

Follow the phases defined in the change proposal:

#### Phase 1: Preparation

```bash
# Create feature branch
git checkout -b feature/{{CHANGE_NAME}}

# Create implementation tracking document
touch storage/changes/{{CHANGE_NAME}}-implementation.md
```

#### Phase 2: Update Requirements

For ADDED requirements:
- Create new requirement files in `storage/specs/`

For MODIFIED requirements:
- Update existing requirement files
- Mark version change

For REMOVED requirements:
- Archive to `storage/archive/`
- Update traceability

#### Phase 3: Update Design

- Update `storage/specs/DES-*.md` files
- Add new ADRs for significant changes

#### Phase 4: Implement Code

Follow Test-First (Article III):

1. **Write Tests (RED)**
   ```typescript
   // packages/core/__tests__/unit/{{feature}}.test.ts
   describe('REQ-{{COMPONENT}}-NEW-001: [New Feature]', () => {
     it('should [new behavior]', () => {
       // Test new functionality
     });
   });
   ```

2. **Implement (GREEN)**
   ```typescript
   // packages/core/src/{{feature}}/service.ts
   // Minimal implementation to pass tests
   ```

3. **Refactor (BLUE)**
   - Improve design
   - Ensure tests still pass

---

### 4. Feature Flag (Optional)

For gradual rollout:

```typescript
// packages/core/src/config/feature-flags.ts

export const FEATURE_FLAGS = {
  enable_{{feature}}: {
    enabled: false,  // Start disabled
    description: '{{CHANGE_DESCRIPTION}}',
  },
} as const;
```

```typescript
// Usage in code
import { FEATURE_FLAGS } from '../config/feature-flags.js';

if (FEATURE_FLAGS.enable_{{feature}}.enabled) {
  // New implementation
} else {
  // Old implementation
}
```

---

### 5. Update CLI (Article II)

If CLI changes:

```typescript
// packages/core/src/cli/commands/{{feature}}.ts

export function register{{Feature}}Command(program: Command): void {
  program
    .command('{{feature}}')
    .description('{{New/Updated description}}')
    .option('--new-option', 'New option from change')
    .action(async (options) => {
      // Updated implementation
    });
}
```

---

### 6. Update MCP Tools

If MCP tools change:

```typescript
// packages/mcp-server/src/tools/{{feature}}-tools.ts

export const {{feature}}Tool: ToolDefinition = {
  name: 'sdd_{{feature}}',
  description: '{{Updated description}}',
  inputSchema: {
    type: 'object',
    properties: {
      // Updated schema
      newProperty: {
        type: 'string',
        description: 'New property from change',
      },
    },
  },
  handler: async (args) => {
    // Updated implementation
  },
};
```

---

### 7. Generate Implementation Report

**Output**: `storage/changes/{{CHANGE_NAME}}-implementation.md`

```markdown
# Implementation Report: {{CHANGE_NAME}}

**Date**: {{DATE}}
**Status**: In Progress / Completed

## Summary

| Item | Status |
|------|--------|
| Requirements Updated | ✅ |
| Design Updated | ✅ |
| Tests Written | ✅ |
| Code Implemented | ✅ |
| Documentation Updated | ⏳ |

## Changes Made

### Files Created

- `packages/core/src/{{feature}}/new-module.ts`
- `packages/core/__tests__/unit/new-module.test.ts`

### Files Modified

- `packages/core/src/{{feature}}/service.ts`
- `packages/mcp-server/src/tools/{{feature}}-tools.ts`

### Files Deleted

- `packages/core/src/{{feature}}/deprecated.ts`

## Test Results

\`\`\`
npm test

✓ packages/core/__tests__/unit/{{feature}}.test.ts (10 tests)
✓ packages/core/__tests__/integration/{{feature}}.integration.test.ts (5 tests)

Test Suites: 2 passed
Tests: 15 passed
Coverage: 87%
\`\`\`

## Traceability Verification

| Requirement | Design | Code | Test |
|-------------|--------|------|------|
| REQ-XXX-NEW-001 | DES-XXX-001 | ✅ | ✅ |
| REQ-XXX-001 (mod) | DES-XXX-001 | ✅ | ✅ |

## Deployment Notes

1. Run migrations (if any)
2. Enable feature flag
3. Monitor metrics

## Rollback Instructions

1. Disable feature flag
2. Revert to previous release
```

---

### 8. Validation

Run all validations:

```bash
# Tests
npm test

# Type check
npm run typecheck

# Lint
npm run lint

# Traceability
npx musubix trace validate
```

---

**MUSUBIX**: https://github.com/nahisaho/MUSUBIX
**Version**: 1.0.0
