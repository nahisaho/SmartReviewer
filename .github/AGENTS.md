# MUSUBIX - AI Coding Agents

This file defines AI agent configurations for MUSUBIX - Neuro-Symbolic AI Integration System.

**Platform Support**: GitHub Copilot, Claude, Cursor, Gemini CLI, Codex CLI, Windsurf

---

## MCP Server Integration

MUSUBIX provides an MCP Server (`@nahisaho/musubix-mcp-server`) with 9 tools and 3 prompts.

### Starting MCP Server

```bash
npx @nahisaho/musubix-mcp-server
npx musubix-mcp --transport stdio
```

### MCP Tools (9 Tools)

| Tool Name | Description | Usage |
|-----------|-------------|-------|
| `sdd_create_requirements` | Create EARS-format requirements document | Requirements phase |
| `sdd_validate_requirements` | Validate requirements against EARS patterns | Requirements validation |
| `sdd_create_design` | Create C4 model design document | Design phase |
| `sdd_validate_design` | Validate design traceability | Design validation |
| `sdd_create_tasks` | Generate implementation tasks | Task breakdown |
| `sdd_query_knowledge` | Query YATA knowledge graph | Knowledge retrieval |
| `sdd_update_knowledge` | Update knowledge graph | Knowledge management |
| `sdd_validate_constitution` | Validate against 9 Constitutional Articles | Compliance check |
| `sdd_validate_traceability` | Validate requirement-design-task traceability | Traceability audit |

### MCP Prompts (3 Prompts)

| Prompt Name | Description |
|-------------|-------------|
| `sdd_requirements_analysis` | Analyze feature and generate EARS requirements |
| `sdd_requirements_review` | Review requirements for completeness |
| `sdd_design_generation` | Generate C4 model design from requirements |

**Setup**: See `steering/tech.ja.md` for configuration.

---

## Project Structure

MUSUBIX is a monorepo with 3 packages:

```
packages/
├── core/           # @nahisaho/musubix-core - CLI, validation, code generation
├── mcp-server/     # @nahisaho/musubix-mcp-server - MCP Server
└── yata-client/    # @nahisaho/musubix-yata-client - Knowledge graph client
```

---

## CLI Commands

```bash
# Project initialization
npx musubix init [path] [--name <name>] [--force]

# Requirements analysis (EARS format)
npx musubix requirements analyze <file>
npx musubix requirements validate <file>
npx musubix requirements map <file>
npx musubix requirements search <query>

# Design generation
npx musubix design generate <file>
npx musubix design patterns <context>
npx musubix design validate <file>
npx musubix design c4 <file>
npx musubix design adr <decision>

# Code generation
npx musubix codegen generate <file>
npx musubix codegen analyze <file>
npx musubix codegen security <path>

# Test generation
npx musubix test generate <file>
npx musubix test coverage <dir>

# Traceability
npx musubix trace matrix
npx musubix trace impact <id>
npx musubix trace validate

# Explanation
npx musubix explain why <id>
npx musubix explain graph <id>
```

---

## 9 Constitutional Articles

All development activities are governed by these immutable rules:

| Article | Name | Summary |
|---------|------|---------|
| **I** | Library-First | Features start as independent libraries in packages/ |
| **II** | CLI Interface | All libraries expose CLI |
| **III** | Test-First | Red-Green-Blue cycle |
| **IV** | EARS Format | Requirements in EARS syntax |
| **V** | Traceability | 100% Requirements↔Design↔Code↔Tests tracking |
| **VI** | Project Memory | Consult steering/ before decisions |
| **VII** | Design Patterns | Document pattern applications |
| **VIII** | Decision Records | All decisions as ADRs |
| **IX** | Quality Gates | Validate before phase transitions |

---

## Prompt Files

GitHub Copilot prompts are located in `.github/prompts/`:

| Prompt | Command | Description |
|--------|---------|-------------|
| `sdd-requirements.prompt.md` | `musubix requirements` | Create EARS requirements |
| `sdd-design.prompt.md` | `musubix design` | Generate C4 design |
| `sdd-tasks.prompt.md` | `musubix tasks` | Break down into tasks |
| `sdd-implement.prompt.md` | `musubix implement` | Execute implementation |
| `sdd-validate.prompt.md` | `musubix validate` | Validate compliance |
| `sdd-steering.prompt.md` | `musubix steering` | Manage project memory |
| `sdd-change-init.prompt.md` | `musubix change init` | Initialize change proposal |
| `sdd-change-apply.prompt.md` | `musubix change apply` | Apply change proposal |
| `sdd-change-archive.prompt.md` | `musubix change archive` | Archive completed change |

---

## Project Memory (Steering)

AI agents MUST consult these files before making decisions:

| File | Content |
|------|---------|
| `steering/structure.ja.md` | Architecture patterns, layer structure |
| `steering/tech.ja.md` | Technology stack (TypeScript, Node.js 20+) |
| `steering/product.ja.md` | Product context |
| `steering/rules/constitution.md` | 9 Constitutional Articles |
| `steering/project.yml` | Project configuration |

---

## Storage Structure

| Path | Content |
|------|---------|
| `storage/specs/` | Requirements (REQ-*), Design (DES-*), Tasks (TSK-*) |
| `storage/design/` | Design documents, C4 diagrams |
| `storage/traceability/` | Traceability matrices |
| `storage/reviews/` | Code reviews, validations |
| `storage/changes/` | Change proposals and implementations |
| `storage/archive/` | Archived documents |

---

## EARS Patterns

All requirements MUST use one of 5 EARS patterns:

| Pattern | Syntax | Example |
|---------|--------|---------|
| **Event-driven** | `WHEN [event], the [system] SHALL [response]` | WHEN user clicks Submit, the system SHALL validate input |
| **State-driven** | `WHILE [state], the [system] SHALL [response]` | WHILE loading, the UI SHALL show spinner |
| **Unwanted** | `IF [error], THEN the [system] SHALL [response]` | IF timeout occurs, THEN the system SHALL retry |
| **Optional** | `WHERE [feature enabled], the [system] SHALL [response]` | WHERE 2FA enabled, the system SHALL require OTP |
| **Ubiquitous** | `The [system] SHALL [requirement]` | The API SHALL authenticate all requests |

---

## C4 Model Levels

Design documents use 4 C4 levels:

| Level | Name | Content |
|-------|------|---------|
| **1** | Context | System boundary, external actors |
| **2** | Container | Deployable units, databases, APIs |
| **3** | Component | Internal structure, services, repositories |
| **4** | Code | Implementation details |

---

## Development Workflow

```
1. Read steering/ (Article VI)
2. Define requirements in EARS format (Article IV)
3. Design with C4 model
4. Write tests first - RED (Article III)
5. Implement minimum code - GREEN
6. Refactor - BLUE
7. Validate traceability (Article V)
8. Pass quality gates (Article IX)
```

---

## Technology Stack

- **Language**: TypeScript
- **Runtime**: Node.js >= 20.0.0
- **Package Manager**: npm >= 10.0.0
- **Build**: npm workspaces (monorepo)
- **Test**: Vitest
- **Lint**: ESLint

---

## Quick Start

```bash
# Initialize project
npx musubix init my-project

# Create requirements
npx musubix requirements analyze feature.md

# Generate design
npx musubix design generate requirements.md

# Break down tasks
npx musubix tasks generate design.md

# Implement with Test-First
npx musubix implement feature-name

# Validate
npx musubix validate feature-name
```

---

**Agent**: GitHub Copilot / Claude
**Last Updated**: 2026-01-02
**Version**: 1.0.0
**Repository**: https://github.com/nahisaho/MUSUBIX
