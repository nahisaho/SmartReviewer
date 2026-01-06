# MUSUBIX Implement Command

Execute implementation tasks for a feature following Test-First principles.

---

## Instructions for AI Agent

You are executing the `musubix implement [feature-name]` command to implement a feature following SDD workflow.

### Command Format

```bash
npx musubix implement authentication
npx musubix codegen generate design.md
```

### Your Task

Implement the feature by executing tasks from the task breakdown document, following Test-First principles (Article III) and constitutional governance.

---

## Process

### 1. Read All Context

**CRITICAL**: Read these files first:

```bash
# Task Breakdown
storage/specs/TSK-{{FEATURE}}-001.md

# Design
storage/specs/DES-{{FEATURE}}-001.md

# Requirements
storage/specs/REQ-{{FEATURE}}-001.md

# Steering Context
steering/structure.ja.md
steering/tech.ja.md
steering/product.ja.md
```

---

### 2. Verify Prerequisites

**Check task breakdown exists**:

```markdown
❌ **Error**: Task breakdown not found

Expected: storage/specs/TSK-{{FEATURE}}-001.md

Please run `npx musubix tasks generate` first.
```

---

### 3. Use Todo Tracking

Track implementation progress:

```markdown
1. TSK-001: Set Up Package Structure
2. TSK-002: Write Tests (RED)
3. TSK-003: Implement Code (GREEN)
4. TSK-004: Refactor (BLUE)
5. TSK-005: CLI Interface (Article II)
6. TSK-006: MCP Tool (if needed)
```

---

### 4. Execute Tasks in Order

#### TSK-001: Set Up Package Structure

**Create structure in appropriate package**:

```
packages/core/src/{{feature}}/
├── index.ts          # Public API exports
├── service.ts        # Business logic
├── types.ts          # TypeScript types
└── errors.ts         # Custom errors

packages/core/__tests__/
├── unit/
│   └── {{feature}}.test.ts
└── integration/
    └── {{feature}}.integration.test.ts
```

**Create public API**:

```typescript
// packages/core/src/{{feature}}/index.ts

/**
 * {{Feature}} Module
 * 
 * @see REQ-{{COMPONENT}}-001
 * @see DES-{{FEATURE}}-001
 */

export { {{Feature}}Service } from './service.js';
export type { {{Feature}}Options, {{Feature}}Result } from './types.js';
```

**Create types**:

```typescript
// packages/core/src/{{feature}}/types.ts

/**
 * @see REQ-{{COMPONENT}}-001
 */
export interface {{Feature}}Options {
  input: string;
  output?: string;
}

export interface {{Feature}}Result {
  success: boolean;
  data?: unknown;
  error?: string;
}
```

---

#### TSK-002: Write Tests (RED Phase) 🔴

**CRITICAL (Article III)**: Tests BEFORE implementation.

```typescript
// packages/core/__tests__/unit/{{feature}}.test.ts

import { describe, it, expect, beforeEach } from 'vitest';
import { {{Feature}}Service } from '../../src/{{feature}}/index.js';

describe('REQ-{{COMPONENT}}-001: {{Requirement Title}}', () => {
  let service: {{Feature}}Service;

  beforeEach(() => {
    service = new {{Feature}}Service();
  });

  // Acceptance Criterion 1
  it('should [acceptance criterion 1]', async () => {
    // Arrange
    const input = { /* ... */ };

    // Act
    const result = await service.process(input);

    // Assert
    expect(result.success).toBe(true);
  });

  // Acceptance Criterion 2
  it('should handle errors gracefully', async () => {
    // Arrange
    const invalidInput = { /* ... */ };

    // Act & Assert
    await expect(service.process(invalidInput)).rejects.toThrow();
  });
});
```

**Run tests** (should FAIL):

```bash
npm test packages/core/__tests__/unit/{{feature}}.test.ts
# Expected: Tests FAIL (service.ts doesn't exist yet)
```

---

#### TSK-003: Implement Code (GREEN Phase) 💚

**Create minimal implementation**:

```typescript
// packages/core/src/{{feature}}/service.ts

import type { {{Feature}}Options, {{Feature}}Result } from './types.js';
import { ValidationError } from './errors.js';

/**
 * {{Feature}} Service
 * 
 * @see REQ-{{COMPONENT}}-001
 * @see DES-{{FEATURE}}-001
 */
export class {{Feature}}Service {
  /**
   * Process {{feature}} request
   * 
   * Acceptance Criteria:
   * - [Criterion 1]
   * - [Criterion 2]
   */
  async process(options: {{Feature}}Options): Promise<{{Feature}}Result> {
    // Validate input
    this.validate(options);

    // Process
    const result = await this.execute(options);

    return {
      success: true,
      data: result,
    };
  }

  private validate(options: {{Feature}}Options): void {
    if (!options.input) {
      throw new ValidationError('input is required');
    }
  }

  private async execute(options: {{Feature}}Options): Promise<unknown> {
    // Minimal implementation
    return { processed: true };
  }
}
```

**Run tests** (should PASS):

```bash
npm test packages/core/__tests__/unit/{{feature}}.test.ts
# Expected: Tests PASS ✅
```

---

#### TSK-004: Refactor (BLUE Phase) 💙

**Improve code while keeping tests green**:

- Extract validators
- Add proper error handling
- Apply SOLID principles
- Improve naming

```bash
npm test packages/core/__tests__/unit/{{feature}}.test.ts
# Expected: Tests still PASS ✅
```

---

#### TSK-005: CLI Command (Article II)

**Create CLI command**:

```typescript
// packages/core/src/cli/commands/{{feature}}.ts

import type { Command } from 'commander';
import { {{Feature}}Service } from '../../{{feature}}/index.js';

/**
 * Register {{feature}} command
 * 
 * @see REQ-CLI-001
 * @see Article II: CLI Interface Mandate
 */
export function register{{Feature}}Command(program: Command): void {
  program
    .command('{{feature}}')
    .description('{{Feature description}}')
    .argument('<input>', 'Input file or value')
    .option('-o, --output <path>', 'Output path')
    .option('--json', 'Output as JSON')
    .action(async (input, options) => {
      const service = new {{Feature}}Service();
      const result = await service.process({ input, ...options });
      
      if (options.json) {
        console.log(JSON.stringify(result, null, 2));
      } else {
        console.log(result);
      }
    });
}
```

**Register in CLI**:

```typescript
// packages/core/src/cli/index.ts

import { register{{Feature}}Command } from './commands/{{feature}}.js';

// In setupCommands function:
register{{Feature}}Command(program);
```

---

#### TSK-006: MCP Tool (if needed)

**Create MCP tool**:

```typescript
// packages/mcp-server/src/tools/{{feature}}-tools.ts

import type { ToolDefinition, ToolResult } from '../types.js';

/**
 * {{Feature}} Tool
 * 
 * @see REQ-MCP-001
 */
export const {{feature}}Tool: ToolDefinition = {
  name: 'sdd_{{feature}}',
  description: '{{Feature description}}',
  inputSchema: {
    type: 'object',
    properties: {
      input: {
        type: 'string',
        description: 'Input value',
      },
    },
    required: ['input'],
  },
  handler: async (args): Promise<ToolResult> => {
    const { input } = args as { input: string };
    
    // Implementation
    return {
      content: [{ type: 'text', text: `Processed: ${input}` }],
    };
  },
};
```

---

### 5. Validation Commands

```bash
# Run all tests
npm test

# Type check
npm run typecheck

# Lint
npm run lint

# Build
npm run build
```

---

### 6. Git Workflow

```bash
# RED phase
git add packages/core/__tests__/
git commit -m "test: add failing tests for REQ-{{COMPONENT}}-001"

# GREEN phase
git add packages/core/src/{{feature}}/
git commit -m "feat: implement REQ-{{COMPONENT}}-001"

# BLUE phase
git commit -m "refactor: improve {{feature}} implementation"

# CLI
git commit -m "feat: add {{feature}} CLI command (Article II)"
```

---

**MUSUBIX**: https://github.com/nahisaho/MUSUBIX
**Version**: 1.0.0
