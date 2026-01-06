# MUSUBIX Steering Command

Generate or update project memory (steering context).

---

## Instructions for AI Agent

You are executing the `musubix steering` command to generate or update the project's steering context.

### What is Steering?

Steering provides **project memory** for AI agents. It consists of core files that document:

1. **structure.ja.md** - Architecture patterns, directory structure
2. **tech.ja.md** - Technology stack, frameworks
3. **product.ja.md** - Business context, product goals
4. **rules/constitution.md** - 9 Constitutional Articles

### Your Task

**Mode Detection**:

1. **Bootstrap Mode** - No steering files exist → Generate initial files
2. **Sync Mode** - Files exist, codebase changed → Update files
3. **Review Mode** - User wants to review → Present and suggest improvements

---

## Mode 1: Bootstrap (First Time)

### Detection

- `steering/` directory doesn't exist OR
- Core files missing

### Steps

1. **Analyze Codebase**:
   - Directory structure
   - Package.json files
   - TypeScript configuration
   - Test framework (Vitest)

2. **Generate Steering Files**:

**Create `steering/structure.ja.md`**:

```markdown
# Project Structure

**Project**: MUSUBIX
**Last Updated**: {{DATE}}

## Architecture Pattern

**Primary Pattern**: Monorepo (npm workspaces)

## Package Structure

\`\`\`
packages/
├── core/           # @nahisaho/musubix-core
├── mcp-server/     # @nahisaho/musubix-mcp-server
└── yata-client/    # @nahisaho/musubix-yata-client
\`\`\`

## Core Package Modules

\`\`\`
packages/core/src/
├── auth/           # Authentication
├── cli/            # CLI Interface (Article II)
├── codegen/        # Code Generation
├── design/         # Design Patterns
├── error/          # Error Handling
├── explanation/    # Explanations
├── requirements/   # Requirements Analysis
├── traceability/   # Traceability
├── types/          # Type Definitions
├── utils/          # Utilities
└── validators/     # EARS Validation
\`\`\`

## Naming Conventions

- Files: `kebab-case.ts`
- Classes: `PascalCase`
- Functions: `camelCase`
- Constants: `SCREAMING_SNAKE_CASE`
```

**Create `steering/tech.ja.md`**:

```markdown
# Technology Stack

**Project**: MUSUBIX
**Last Updated**: {{DATE}}

## Core Technologies

| Category | Technology | Version |
|----------|------------|---------|
| Language | TypeScript | ^5.3 |
| Runtime | Node.js | >= 20.0.0 |
| Package Manager | npm | >= 10.0.0 |
| Build | npm workspaces | - |
| Test | Vitest | ^1.0.0 |
| Lint | ESLint | ^8.0.0 |

## Package Dependencies

### @nahisaho/musubix-core

- commander: CLI framework
- chalk: Terminal styling

### @nahisaho/musubix-mcp-server

- MCP protocol support

### @nahisaho/musubix-yata-client

- Knowledge graph client

## Development Tools

- TypeScript strict mode
- ESM modules (`"type": "module"`)
- Vitest for testing
```

**Create `steering/product.ja.md`**:

```markdown
# Product Context

**Project**: MUSUBIX
**Last Updated**: {{DATE}}

## Product Vision

Neuro-Symbolic AI Integration System that combines:
- **Neural (LLM)**: Creative code generation
- **Symbolic (YATA)**: Knowledge graph precision

## Target Users

- Software Developers
- AI/ML Engineers
- Development Teams

## Core Features

1. EARS Requirements Analysis
2. C4 Model Design Generation
3. Test-First Development
4. Complete Traceability
5. MCP Server Integration
```

---

## Mode 2: Sync (Update Existing)

### Detection

- Steering files exist
- Codebase has changes

### Steps

1. **Compare Current State**:
   - Read existing steering files
   - Analyze current codebase
   - Identify discrepancies

2. **Update Files**:
   - Add new modules/packages
   - Update technology versions
   - Reflect architecture changes

3. **Generate Diff Report**:

```markdown
## Steering Sync Report

### Changes Detected

| File | Change | Action |
|------|--------|--------|
| structure.ja.md | New module: utils/ | Updated |
| tech.ja.md | Vitest 1.0 → 2.0 | Updated |

### Files Updated

1. `steering/structure.ja.md` - Added utils module
2. `steering/tech.ja.md` - Updated Vitest version
```

---

## Mode 3: Review

### Steps

1. **Present Current Steering**:
   - Show structure.ja.md content
   - Show tech.ja.md content
   - Show product.ja.md content

2. **Analyze for Improvements**:
   - Missing documentation
   - Outdated information
   - Inconsistencies

3. **Suggest Improvements**:

```markdown
## Steering Review

### Current State

✅ structure.ja.md - Complete
✅ tech.ja.md - Complete
⚠️ product.ja.md - Missing user personas

### Recommendations

1. Add user personas to product.ja.md
2. Update tech stack versions
3. Add ADR index
```

---

## Constitutional Articles Reference

Always include reference to `steering/rules/constitution.md`:

| Article | Name | Summary |
|---------|------|---------|
| I | Library-First | Features in packages/ |
| II | CLI Interface | CLI for all libraries |
| III | Test-First | Red-Green-Blue |
| IV | EARS Format | Requirements syntax |
| V | Traceability | 100% tracking |
| VI | Project Memory | Read steering first |
| VII | Design Patterns | Document patterns |
| VIII | Decision Records | ADRs for decisions |
| IX | Quality Gates | Validate phases |

---

## Output

Save steering files to:

- `steering/structure.ja.md`
- `steering/tech.ja.md`
- `steering/product.ja.md`
- `steering/rules/constitution.md`
- `steering/project.yml`

---

**MUSUBIX**: https://github.com/nahisaho/MUSUBIX
**Version**: 1.0.0
