# MUSUBIX Design Command

Generate technical design from requirements using C4 model.

---

## Instructions for AI Agent

You are executing the `musubix design [feature-name]` command to create a technical design specification.

### Command Format

```bash
npx musubix design generate requirements.md
npx musubix design patterns context
npx musubix design validate design.md
npx musubix design c4 design.md
npx musubix design adr decision
```

### Your Task

Generate a comprehensive technical design that implements the requirements while adhering to constitutional governance.

---

## Process

### 1. Read Context (Article VI)

**CRITICAL**: Read these files BEFORE designing:

```bash
# Steering Context
steering/structure.ja.md    # Architecture patterns to follow
steering/tech.ja.md         # Technology stack (TypeScript, Node.js 20+)
steering/product.ja.md      # Product goals and users

# Requirements
storage/specs/REQ-{{FEATURE}}-001.md  # What to implement
```

---

### 2. Verify Requirements Exist

**If NOT found**:

```markdown
❌ **Requirements file not found**

Expected: storage/specs/REQ-{{FEATURE}}-001.md

Please run `npx musubix requirements analyze {{feature}}` first.

Design cannot proceed without requirements (Article V: Traceability).
```

---

### 3. Generate Design Document (C4 Model)

**Output**: `storage/specs/DES-{{FEATURE}}-001.md`

#### A. Context Diagram (Level 1)

- System boundary
- External users
- External systems

#### B. Container Diagram (Level 2)

MUSUBIX architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    MUSUBIX System                        │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ @nahisaho/      │  │ @nahisaho/      │               │
│  │ musubix-core    │←→│ musubix-mcp-    │               │
│  │                 │  │ server          │               │
│  └────────┬────────┘  └────────┬────────┘               │
│           │                    │                         │
│           │    ┌───────────────┘                         │
│           │    │                                         │
│           ▼    ▼                                         │
│  ┌─────────────────┐                                    │
│  │ @nahisaho/      │                                    │
│  │ musubix-yata-   │                                    │
│  │ client          │                                    │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
```

#### C. Component Diagram (Level 3)

For packages/core/:

```
packages/core/src/
├── auth/           # Authentication & Authorization
├── cli/            # CLI Interface (Article II)
├── codegen/        # Code Generation & Analysis
├── design/         # Design Patterns & C4 Models
├── error/          # Error Handling
├── explanation/    # Explanation Generation
├── requirements/   # Requirements Analysis
├── traceability/   # Traceability
├── types/          # Type Definitions
├── utils/          # Utilities
└── validators/     # EARS Validation
```

---

### 4. Requirements Mapping (Article V)

**CRITICAL**: Map EVERY requirement to design decisions.

```markdown
| Component | Requirements | Design Rationale |
|-----------|--------------|------------------|
| CLI | REQ-CLI-001 | Command interface |
| Validator | REQ-EARS-001 | EARS pattern validation |
| MCP Server | REQ-MCP-001 | Tool/prompt exposure |
```

---

### 5. API Design

For CLI commands:

```typescript
// packages/core/src/cli/commands/{{feature}}.ts

export interface {{Feature}}Options {
  input: string;
  output?: string;
  format?: 'json' | 'markdown';
}

export async function {{feature}}Command(options: {{Feature}}Options): Promise<void> {
  // REQ-{{COMPONENT}}-001: [Requirement title]
}
```

For MCP tools:

```typescript
// packages/mcp-server/src/tools/{{feature}}-tools.ts

export const {{feature}}Tool: ToolDefinition = {
  name: 'sdd_{{feature}}',
  description: '{{Feature description}}',
  inputSchema: {
    type: 'object',
    properties: {
      // ...
    },
    required: ['...'],
  },
  handler: async (args) => {
    // REQ-{{COMPONENT}}-001
  },
};
```

---

### 6. Design Document Template

```markdown
# Design Document: {{FEATURE_NAME}}

**Document ID**: DES-{{FEATURE}}-001
**Version**: 1.0.0
**Date**: {{DATE}}
**Requirements**: REQ-{{FEATURE}}-001

## Overview

- **Purpose**: [Design purpose]
- **Package**: packages/core/ | packages/mcp-server/ | packages/yata-client/

## C4 Model

### Level 1: Context
[Context diagram]

### Level 2: Container
[Container diagram]

### Level 3: Component
[Component diagram]

## Requirements Traceability

| Requirement | Component | Implementation |
|-------------|-----------|----------------|
| REQ-XXX-001 | cli/commands/{{feature}}.ts | {{Feature}}Command |

## API Design

### CLI Interface (Article II)

\`\`\`bash
npx musubix {{feature}} [options]
\`\`\`

### TypeScript Interface

\`\`\`typescript
export interface {{Feature}}Options {
  // ...
}
\`\`\`

## ADR (Architecture Decision Records)

### ADR-001: [Decision Title]

**Status**: Accepted
**Context**: [Why was this decision needed?]
**Decision**: [What was decided?]
**Consequences**: [What are the results?]

## Traceability

- **Requirements**: REQ-{{FEATURE}}-001
- **Tasks**: TSK-{{FEATURE}}-001
- **Tests**: packages/core/__tests__/unit/{{feature}}.test.ts
```

---

### 7. MCP Tool Integration

Use MUSUBIX MCP tools:

```
sdd_create_design - Create design document
sdd_validate_design - Validate traceability
```

---

**MUSUBIX**: https://github.com/nahisaho/MUSUBIX
**Version**: 1.0.0
