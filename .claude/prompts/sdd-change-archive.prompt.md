# MUSUBIX Change Archive Command

Archive a completed change proposal.

---

## Instructions for AI Agent

You are executing the `musubix change archive [change-name]` command to archive a completed change.

### Command Format

```bash
npx musubix change archive add-2fa
npx musubix change archive migrate-to-graphql
```

### Your Task

Archive the change proposal and implementation, update documentation, and clean up.

---

## Process

### 1. Verify Change Completion

**Read Implementation Report**:

```bash
storage/changes/{{CHANGE_NAME}}-implementation.md
```

**Verify Status**:

- [ ] Implementation report exists
- [ ] All requirements implemented
- [ ] Tests passing
- [ ] Feature flag enabled (or deprecated feature removed)

**If Not Complete**:

```markdown
⚠️ **Change not ready for archival**

Status Check:
- [ ] Implementation complete
- [ ] Tests passing
- [ ] Deployed
- [ ] Stable period passed

Please complete all steps before archiving.
```

---

### 2. Collect Final Metrics

```markdown
## Final Metrics: {{CHANGE_NAME}}

### Test Results

- Unit Tests: XX passed
- Integration Tests: XX passed
- Coverage: XX%

### Code Quality

- Lint: ✅ No errors
- TypeScript: ✅ No errors

### Traceability

- Requirements Coverage: 100%
- Design Coverage: 100%
- Test Coverage: XX%
```

---

### 3. Archive Documents

Move change documents to archive:

```bash
# Create archive directory
mkdir -p storage/archive/changes/{{CHANGE_NAME}}

# Move change documents
mv storage/changes/{{CHANGE_NAME}}-proposal.md storage/archive/changes/{{CHANGE_NAME}}/
mv storage/changes/{{CHANGE_NAME}}-implementation.md storage/archive/changes/{{CHANGE_NAME}}/
```

---

### 4. Update Main Documentation

**Update Traceability Matrix**:

Add entries to `storage/traceability/`:

```markdown
## Change: {{CHANGE_NAME}}

**Archived**: {{DATE}}

| Requirement | Design | Task | Code | Test |
|-------------|--------|------|------|------|
| REQ-XXX-NEW-001 | DES-XXX-001 | TSK-XXX-001 | service.ts | service.test.ts |
```

**Update CHANGELOG.md**:

```markdown
## [1.x.x] - {{DATE}}

### Added
- {{Feature description}} (CHG-{{CHANGE}}-001)

### Changed
- {{Modified feature}} (CHG-{{CHANGE}}-001)

### Removed
- {{Deprecated feature}} (CHG-{{CHANGE}}-001)
```

---

### 5. Remove Feature Flags (if applicable)

If feature flag was used:

```typescript
// packages/core/src/config/feature-flags.ts

// REMOVE:
// enable_{{feature}}: {
//   enabled: true,
//   description: '{{CHANGE_DESCRIPTION}}',
// },

// Update code to remove flag checks
```

---

### 6. Generate Archive Summary

**Output**: `storage/archive/changes/{{CHANGE_NAME}}/SUMMARY.md`

```markdown
# Change Archive Summary: {{CHANGE_NAME}}

**Document ID**: CHG-{{CHANGE}}-001
**Archived**: {{DATE}}
**Duration**: X weeks

## Overview

**Change Type**: Feature / Enhancement / Refactor
**Packages Affected**: packages/core/, packages/mcp-server/

## Final State

### Requirements

| ID | Title | Status |
|----|-------|--------|
| REQ-XXX-NEW-001 | [New Feature] | Implemented |
| REQ-XXX-001 | [Modified Feature] | Updated |

### Files Changed

**Created**: X files
**Modified**: X files
**Deleted**: X files

### Test Coverage

- Before: XX%
- After: XX%

## Documents Archived

1. {{CHANGE_NAME}}-proposal.md
2. {{CHANGE_NAME}}-implementation.md
3. SUMMARY.md (this file)

## Lessons Learned

1. [Lesson 1]
2. [Lesson 2]

## Related Changes

- CHG-XXX-001: [Related change]
```

---

### 7. Clean Up

```bash
# Remove any temporary files
rm -rf storage/changes/{{CHANGE_NAME}}-*.tmp

# Verify archive is complete
ls storage/archive/changes/{{CHANGE_NAME}}/
# Expected:
# - {{CHANGE_NAME}}-proposal.md
# - {{CHANGE_NAME}}-implementation.md
# - SUMMARY.md

# Git commit
git add storage/archive/changes/{{CHANGE_NAME}}/
git add storage/traceability/
git add CHANGELOG.md
git commit -m "chore: archive change CHG-{{CHANGE}}-001"
```

---

### 8. Final Verification

```bash
# Ensure no orphaned references
grep -r "CHG-{{CHANGE}}-001" packages/
# Should only find documentation references

# Ensure tests still pass
npm test

# Ensure build succeeds
npm run build
```

---

**MUSUBIX**: https://github.com/nahisaho/MUSUBIX
**Version**: 1.0.0
