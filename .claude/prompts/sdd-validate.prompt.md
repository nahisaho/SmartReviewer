# MUSUBIX Validate Command

Validate constitutional compliance and requirements coverage.

---

## Instructions for AI Agent

You are executing the `musubix validate [feature-name]` command to validate constitutional compliance.

### Command Format

```bash
npx musubix validate authentication
npx musubix trace validate
npx musubix trace matrix
```

### Your Task

Perform comprehensive validation of the feature implementation against:

1. 9 Constitutional Articles
2. Requirements coverage (100% traceability)
3. Code quality standards
4. Test coverage

---

## Process

### 1. Read All Documentation

```bash
# Requirements and Design
storage/specs/REQ-{{FEATURE}}-001.md
storage/specs/DES-{{FEATURE}}-001.md
storage/specs/TSK-{{FEATURE}}-001.md

# Steering Context
steering/structure.ja.md
steering/tech.ja.md
steering/rules/constitution.md

# Source Code
packages/core/src/{{feature}}/**/*.ts
packages/core/__tests__/**/*.test.ts
packages/mcp-server/src/tools/**/*.ts
```

---

### 2. Constitutional Validation

Validate each of the 9 Constitutional Articles:

#### Article I: Library-First Principle

**Requirement**: Features as independent packages

**Validation**:
- [ ] Feature in `packages/` directory
- [ ] Has `package.json` (monorepo workspace)
- [ ] Exports public API via `index.ts`
- [ ] No circular dependencies

```markdown
### Article I: Library-First Principle

**Status**: ✅ PASS / ❌ FAIL

**Evidence**:
- Location: `packages/core/src/{{feature}}/`
- Public API: `packages/core/src/{{feature}}/index.ts`
- Exports: {{Feature}}Service, {{Feature}}Options
```

---

#### Article II: CLI Interface Mandate

**Requirement**: CLI interface for all libraries

**Validation**:
- [ ] CLI command exists in `packages/core/src/cli/commands/`
- [ ] `--help` flag works
- [ ] Documented in CLI help

```markdown
### Article II: CLI Interface Mandate

**Status**: ✅ PASS / ❌ FAIL

**Evidence**:
- CLI: `npx musubix {{feature}}`
- Help: `npx musubix {{feature}} --help`
- Registered: packages/core/src/cli/index.ts
```

---

#### Article III: Test-First Imperative

**Requirement**: Tests before implementation (Red-Green-Blue)

**Validation**:
- [ ] Tests in `packages/core/__tests__/unit/`
- [ ] Tests cover all requirements
- [ ] Coverage ≥ 80%

```bash
npm run test:coverage
```

```markdown
### Article III: Test-First Imperative

**Status**: ✅ PASS / ❌ FAIL

**Coverage**: XX%
**Test Files**:
- packages/core/__tests__/unit/{{feature}}.test.ts
- packages/core/__tests__/integration/{{feature}}.integration.test.ts
```

---

#### Article IV: EARS Requirements Format

**Requirement**: All requirements in EARS format

**Validation**:
- [ ] All requirements use EARS patterns
- [ ] Each has unique ID (REQ-XXX-NNN)
- [ ] Each has acceptance criteria

```markdown
### Article IV: EARS Requirements Format

**Status**: ✅ PASS / ❌ FAIL

**Requirements Checked**: X
**EARS Patterns Used**:
- Ubiquitous: X
- Event-driven: X
- State-driven: X
- Unwanted: X
- Optional: X
```

---

#### Article V: Traceability Mandate

**Requirement**: 100% traceability REQ↔DES↔TSK↔CODE↔TEST

**Validation**:

```markdown
### Article V: Traceability Mandate

**Status**: ✅ PASS / ❌ FAIL

**Traceability Matrix**:

| Requirement | Design | Task | Code | Test |
|-------------|--------|------|------|------|
| REQ-XXX-001 | DES-XXX-001 | TSK-XXX-001 | {{feature}}/service.ts | {{feature}}.test.ts |

**Coverage**: 100%
**Unmapped Requirements**: None
```

---

#### Article VI: Project Memory (Steering)

**Requirement**: Consult steering before decisions

**Validation**:
- [ ] Design references steering files
- [ ] Tech stack matches `steering/tech.ja.md`
- [ ] Architecture matches `steering/structure.ja.md`

---

#### Article VII: Design Patterns

**Requirement**: Document pattern applications

**Validation**:
- [ ] Patterns documented in design
- [ ] ADRs created for decisions

---

#### Article VIII: Decision Records

**Requirement**: All decisions as ADRs

**Validation**:
- [ ] ADRs in design document
- [ ] Each ADR has: Status, Context, Decision, Consequences

---

#### Article IX: Quality Gates

**Requirement**: Validate before phase transitions

**Validation**:
- [ ] Requirements validated before design
- [ ] Design validated before implementation
- [ ] Tests pass before deployment

---

### 3. Generate Validation Report

```markdown
# Validation Report: {{FEATURE_NAME}}

**Date**: {{DATE}}
**Validator**: AI Agent

## Summary

| Article | Status | Score |
|---------|--------|-------|
| I. Library-First | ✅ | 100% |
| II. CLI Interface | ✅ | 100% |
| III. Test-First | ✅ | 85% |
| IV. EARS Format | ✅ | 100% |
| V. Traceability | ✅ | 100% |
| VI. Project Memory | ✅ | 100% |
| VII. Design Patterns | ✅ | 100% |
| VIII. Decision Records | ✅ | 100% |
| IX. Quality Gates | ✅ | 100% |

**Overall Compliance**: ✅ PASS (97%)

## Test Coverage

- Unit Tests: XX%
- Integration Tests: XX%
- Total: XX%

## Traceability Coverage

- Requirements → Design: 100%
- Design → Tasks: 100%
- Tasks → Code: 100%
- Code → Tests: 100%

## Issues Found

### Critical (P0)
None

### High (P1)
None

### Medium (P2)
- [Issue description]

## Recommendations

1. [Recommendation 1]
2. [Recommendation 2]
```

---

### 4. MCP Tool Integration

Use MUSUBIX MCP tools:

```
sdd_validate_constitution - Validate constitutional compliance
sdd_validate_traceability - Validate traceability matrix
```

---

### 5. Validation Commands

```bash
# Run all validations
npm test
npm run typecheck
npm run lint

# Check coverage
npm run test:coverage

# Traceability
npx musubix trace matrix
npx musubix trace validate
```

---

**MUSUBIX**: https://github.com/nahisaho/MUSUBIX
**Version**: 1.0.0
