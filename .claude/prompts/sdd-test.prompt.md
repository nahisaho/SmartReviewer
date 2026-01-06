# MUSUBIX Test Generation Command

Generate comprehensive tests following Test-First (Red-Green-Blue) methodology.

---

## Instructions for AI Agent

You are executing the `musubix test [feature-name]` command to generate tests.

### Command Format

```bash
npx musubix test generate <file>
npx musubix test coverage <dir>
```

### Your Task

Generate comprehensive tests following:

1. Test-First (Red-Green-Blue) methodology
2. EARS requirements coverage
3. Result Type testing patterns
4. Status transition testing

---

## Process

### 1. Read Requirements and Design

```bash
# Requirements (for test cases)
storage/specs/REQ-{{FEATURE}}-001.md

# Design (for component structure)
storage/specs/DES-{{FEATURE}}-001.md

# Existing implementation
packages/core/src/{{feature}}/**/*.ts
```

### 2. Test Categories

Generate tests for each category:

| Category | Coverage Target | Priority |
|----------|-----------------|----------|
| Unit Tests | Functions, Value Objects | P0 |
| Integration Tests | Services, Repositories | P0 |
| E2E Tests | Full workflows | P1 |
| Edge Cases | Boundary conditions | P0 |
| Error Cases | Error handling | P0 |

### 3. Test Structure

```typescript
import { describe, it, expect, beforeEach } from 'vitest';

describe('FeatureName', () => {
  beforeEach(() => {
    // Reset counters for deterministic IDs
    resetFeatureCounter();
  });

  describe('creation', () => {
    it('should create valid entity', () => {
      // Arrange
      const input = { ... };
      
      // Act
      const result = createEntity(input);
      
      // Assert
      expect(result.isOk()).toBe(true);
      if (result.isOk()) {
        expect(result.value.id).toMatch(/^ENT-\d{8}-001$/);
      }
    });

    it('should reject invalid input', () => {
      // Arrange
      const input = { invalid: true };
      
      // Act
      const result = createEntity(input);
      
      // Assert
      expect(result.isErr()).toBe(true);
      if (result.isErr()) {
        expect(result.error.message).toContain('validation');
      }
    });
  });
});
```

### 4. EARS Requirements Mapping

Each requirement must have corresponding tests:

```typescript
/**
 * REQ-AUTH-001: WHEN user provides valid credentials,
 * THEN the system SHALL authenticate the user.
 */
describe('REQ-AUTH-001: User Authentication', () => {
  it('should authenticate user with valid credentials', async () => {
    // Test implementation
  });
});
```

### 5. Result Type Test Patterns

```typescript
// ✅ Test both success and failure cases
describe('createPrice', () => {
  it('should create valid price', () => {
    const result = createPrice(1000);
    expect(result.isOk()).toBe(true);
    if (result.isOk()) {
      expect(result.value.amount).toBe(1000);
    }
  });

  it('should reject price below minimum', () => {
    const result = createPrice(50);
    expect(result.isErr()).toBe(true);
    if (result.isErr()) {
      expect(result.error.message).toContain('100');
    }
  });
});
```

### 6. Status Transition Testing

```typescript
describe('Status Transitions', () => {
  const validTransitions: [Status, Status][] = [
    ['draft', 'active'],
    ['active', 'completed'],
    ['active', 'cancelled'],
  ];

  const invalidTransitions: [Status, Status][] = [
    ['completed', 'active'],
    ['cancelled', 'draft'],
  ];

  validTransitions.forEach(([from, to]) => {
    it(`should allow transition from ${from} to ${to}`, () => {
      const entity = createEntityWithStatus(from);
      const result = entity.transitionTo(to);
      expect(result.isOk()).toBe(true);
    });
  });

  invalidTransitions.forEach(([from, to]) => {
    it(`should reject transition from ${from} to ${to}`, () => {
      const entity = createEntityWithStatus(from);
      const result = entity.transitionTo(to);
      expect(result.isErr()).toBe(true);
    });
  });
});
```

---

## Output Format

```markdown
# Test Generation Report: {{FEATURE}}

## Summary
- **Test Files Created**: X
- **Test Cases**: X total (X unit, X integration, X e2e)
- **Requirements Covered**: X/Y (Z%)

## Generated Test Files

### packages/core/__tests__/{{feature}}/entity.test.ts
- X test cases
- Covers: REQ-XXX-001, REQ-XXX-002

### packages/core/__tests__/{{feature}}/service.test.ts
- X test cases
- Covers: REQ-XXX-003, REQ-XXX-004

## Requirements Coverage Matrix

| Requirement | Test File | Test Cases | Status |
|-------------|-----------|------------|--------|
| REQ-XXX-001 | entity.test.ts | 3 | ✅ |
| REQ-XXX-002 | entity.test.ts | 2 | ✅ |
| REQ-XXX-003 | service.test.ts | 4 | ✅ |

## Run Tests

\`\`\`bash
npm run test -- packages/core/__tests__/{{feature}}/
npm run test:coverage
\`\`\`
```

---

## Traceability

This skill implements:
- **Article III**: Test-First Imperative (テスト先行開発)
- **Article V**: Traceability Mandate (要件↔テストの追跡)

---

## Related Commands

```bash
# Generate tests
npx musubix test generate <file>

# Run tests with coverage
npm run test:coverage

# Validate traceability
npx musubix trace validate
```
