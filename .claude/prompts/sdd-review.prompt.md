# MUSUBIX Code Review Command

Perform comprehensive code review with SOLID principles and quality checks.

---

## Instructions for AI Agent

You are executing the `musubix review [feature-name]` command to perform code review.

### Command Format

```bash
npx musubix codegen analyze <file>
npx musubix trace validate
```

### Your Task

Perform comprehensive code review focusing on:

1. SOLID Principles Compliance
2. Code Quality Metrics
3. Design Pattern Usage
4. Traceability Verification
5. Best Practices Adherence

---

## Process

### 1. Read Source Code and Context

```bash
# Source Code
packages/core/src/{{feature}}/**/*.ts
packages/mcp-server/src/tools/**/*.ts

# Design Documentation
storage/specs/DES-{{FEATURE}}-001.md

# Steering Context
steering/structure.ja.md
steering/tech.ja.md
steering/rules/constitution.md
```

### 2. SOLID Principles Check

Review each file for:

| Principle | Check |
|-----------|-------|
| **S**ingle Responsibility | 1つのクラス/関数は1つの責務のみ |
| **O**pen/Closed | 拡張に開き、修正に閉じている |
| **L**iskov Substitution | 派生クラスは基底クラスと置換可能 |
| **I**nterface Segregation | クライアント固有のインターフェース |
| **D**ependency Inversion | 抽象に依存、具象に依存しない |

### 3. Code Quality Metrics

Analyze:

- **Cyclomatic Complexity**: 関数あたり10以下
- **Lines per Function**: 50行以下
- **Lines per File**: 300行以下
- **Nesting Depth**: 3レベル以下
- **Parameter Count**: 5個以下

### 4. Design Pattern Review

Check for:

- [ ] Repository Pattern (データアクセス)
- [ ] Service Layer (ビジネスロジック)
- [ ] Factory Pattern (オブジェクト生成)
- [ ] Value Objects (ドメイン概念)
- [ ] Result Type (エラーハンドリング)

### 5. Best Practices Check

| カテゴリ | チェック項目 |
|---------|-------------|
| 命名規則 | PascalCase (型), camelCase (変数/関数), UPPER_CASE (定数) |
| TypeScript | strict mode, 明示的な型定義, any禁止 |
| エラー処理 | Result<T, E>パターン, 適切なエラーメッセージ |
| コメント | JSDoc形式, 複雑なロジックの説明 |
| インポート | 絶対パス, 循環参照なし |

---

## Output Format

```markdown
# Code Review Report: {{FEATURE}}

## Summary
- **Overall Score**: A/B/C/D/F
- **Files Reviewed**: X files
- **Issues Found**: X critical, X warnings, X suggestions

## SOLID Compliance
| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | ✅/⚠️/❌ | ... |
| OCP | ✅/⚠️/❌ | ... |
| LSP | ✅/⚠️/❌ | ... |
| ISP | ✅/⚠️/❌ | ... |
| DIP | ✅/⚠️/❌ | ... |

## Quality Metrics
| Metric | Value | Status |
|--------|-------|--------|
| Avg Cyclomatic Complexity | X | ✅/⚠️/❌ |
| Max Lines per Function | X | ✅/⚠️/❌ |
| Max Nesting Depth | X | ✅/⚠️/❌ |

## Issues

### Critical (Must Fix)
1. [FILE:LINE] Description

### Warnings (Should Fix)
1. [FILE:LINE] Description

### Suggestions (Nice to Have)
1. [FILE:LINE] Description

## Recommendations
1. ...
2. ...
```

---

## Traceability

This skill implements:
- **Article III**: Test-First Imperative (コードレビューによる品質確保)
- **Article VII**: Simplicity Gate (コードの複雑性チェック)

---

## Related Commands

```bash
# Static analysis
npx musubix codegen analyze <file>

# Traceability validation
npx musubix trace validate

# Security scanning
npx musubix codegen security <path>
```
