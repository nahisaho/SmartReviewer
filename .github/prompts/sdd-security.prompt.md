# MUSUBIX Security Scan Command

Perform comprehensive security scanning and vulnerability detection.

---

## Instructions for AI Agent

You are executing the `musubix security [feature-name]` command to perform security analysis.

### Command Format

```bash
npx musubix codegen security <path>
```

### Your Task

Perform comprehensive security analysis covering:

1. OWASP Top 10 vulnerabilities
2. Dependency vulnerabilities
3. Authentication/Authorization issues
4. Data validation gaps
5. Sensitive data exposure

---

## Process

### 1. Read Source Code and Dependencies

```bash
# Source Code
packages/core/src/{{feature}}/**/*.ts
packages/mcp-server/src/tools/**/*.ts

# Dependencies
package.json
package-lock.json

# Auth module
packages/core/src/auth/**/*.ts
```

### 2. OWASP Top 10 Checks

| # | Vulnerability | Check |
|---|--------------|-------|
| A01 | Broken Access Control | 認可チェックの実装確認 |
| A02 | Cryptographic Failures | 暗号化の適切な使用 |
| A03 | Injection | SQL/NoSQL/コマンドインジェクション |
| A04 | Insecure Design | セキュリティパターンの適用 |
| A05 | Security Misconfiguration | 設定の安全性 |
| A06 | Vulnerable Components | 依存関係の脆弱性 |
| A07 | Authentication Failures | 認証の実装不備 |
| A08 | Software/Data Integrity | データ整合性の検証 |
| A09 | Security Logging | ログと監視 |
| A10 | SSRF | サーバーサイドリクエストフォージェリ |

### 3. Code Pattern Analysis

#### ❌ Dangerous Patterns

```typescript
// SQL Injection - 危険
const query = `SELECT * FROM users WHERE id = ${userId}`;

// Command Injection - 危険
exec(`ls ${userInput}`);

// Path Traversal - 危険
const file = fs.readFileSync(`./uploads/${filename}`);

// Hardcoded Secrets - 危険
const apiKey = 'sk-1234567890abcdef';

// eval() - 危険
eval(userInput);
```

#### ✅ Safe Patterns

```typescript
// Parameterized Query - 安全
const query = db.query('SELECT * FROM users WHERE id = ?', [userId]);

// Input Validation - 安全
const sanitized = sanitize(userInput);

// Path Validation - 安全
const safePath = path.resolve('./uploads', path.basename(filename));

// Environment Variables - 安全
const apiKey = process.env.API_KEY;

// No eval - 安全
const result = JSON.parse(jsonString);
```

### 4. Authentication & Authorization

Check for:

- [ ] JWT/Session token validation
- [ ] Password hashing (bcrypt, argon2)
- [ ] Role-based access control (RBAC)
- [ ] Rate limiting
- [ ] CSRF protection
- [ ] Secure cookie flags

### 5. Data Validation

```typescript
// ✅ Recommended: Zod schema validation
import { z } from 'zod';

const UserInputSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(100),
  age: z.number().int().positive().max(150),
});

// Validate all user inputs
const result = UserInputSchema.safeParse(userInput);
if (!result.success) {
  return err(new ValidationError(result.error));
}
```

### 6. Dependency Audit

```bash
# Check for known vulnerabilities
npm audit
npm audit --audit-level=moderate

# Update vulnerable packages
npm audit fix
```

---

## Output Format

```markdown
# Security Scan Report: {{FEATURE}}

## Summary
- **Risk Level**: Critical/High/Medium/Low
- **Vulnerabilities Found**: X critical, X high, X medium, X low
- **Dependencies Audited**: X packages

## OWASP Top 10 Assessment

| Category | Status | Findings |
|----------|--------|----------|
| A01: Access Control | ✅/⚠️/❌ | ... |
| A02: Cryptographic | ✅/⚠️/❌ | ... |
| A03: Injection | ✅/⚠️/❌ | ... |
| A04: Insecure Design | ✅/⚠️/❌ | ... |
| A05: Misconfiguration | ✅/⚠️/❌ | ... |
| A06: Vulnerable Deps | ✅/⚠️/❌ | ... |
| A07: Auth Failures | ✅/⚠️/❌ | ... |
| A08: Integrity | ✅/⚠️/❌ | ... |
| A09: Logging | ✅/⚠️/❌ | ... |
| A10: SSRF | ✅/⚠️/❌ | ... |

## Critical Vulnerabilities

### 1. [CRITICAL] SQL Injection in user-service.ts
- **Location**: packages/core/src/user/user-service.ts:45
- **Description**: User input directly concatenated in SQL query
- **Remediation**: Use parameterized queries
- **Reference**: CWE-89

### 2. [HIGH] Hardcoded API Key
- **Location**: packages/core/src/auth/config.ts:12
- **Description**: API key stored in source code
- **Remediation**: Use environment variables
- **Reference**: CWE-798

## Dependency Vulnerabilities

| Package | Severity | Version | Fixed In |
|---------|----------|---------|----------|
| lodash | High | 4.17.20 | 4.17.21 |

## Recommendations

1. **Immediate**: Fix all critical vulnerabilities
2. **Short-term**: Update vulnerable dependencies
3. **Long-term**: Implement security testing in CI/CD

## Compliance Checklist

- [ ] Input validation on all user inputs
- [ ] Output encoding for XSS prevention
- [ ] Parameterized queries for database access
- [ ] Secrets in environment variables
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Audit logging enabled
```

---

## Traceability

This skill implements:
- **Article IX**: Integration-First Testing (セキュリティテスト)
- Security requirements validation

---

## Related Commands

```bash
# Security scan
npx musubix codegen security <path>

# Dependency audit
npm audit

# Static analysis
npx musubix codegen analyze <file>
```
