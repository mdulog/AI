# Naming Conventions

This project is a pure-markdown Claude Code skill. Naming conventions apply to file names, folder names, YAML frontmatter identifiers, and the naming patterns imposed on generated output in target projects.

## Agent File Naming

### Required: Kebab-Case Matching the `name` Field

Every agent file uses kebab-case for its filename, and the filename (without extension) exactly matches the `name` field in the YAML frontmatter.

| File | `name` field |
|---|---|
| `spec-brainstormer.md` | `spec-brainstormer` |
| `spec-writer.md` | `spec-writer` |
| `conventions-writer.md` | `conventions-writer` |
| `legacy-doc-consolidator.md` | `legacy-doc-consolidator` |
| `adr-writer.md` | `adr-writer` |
| `spec-auditor.md` | `spec-auditor` |

This alignment is load-bearing: the orchestrator's STEP 0 verification checks for files by path (`.claude/agents/{name}.md`), and the Agent tool invokes agents by their `name` field.

### Required: Agent Name Pattern

Agent names follow a `{function}-{role}` pattern, where:

- The first segment describes the primary function or domain (`spec`, `conventions`, `legacy-doc`, `adr`).
- The second segment describes the agent's role (`brainstormer`, `writer`, `consolidator`, `auditor`).

All six agents follow this pattern consistently.

## Command File Naming

### Required: Kebab-Case for Command Files

The orchestrator command file uses kebab-case: `generate-knowledge-base.md`. This becomes the slash-command name in Claude Code: `/generate-knowledge-base`.

The command filename matches the project directory name (`generate-knowledge-base/generate-knowledge-base.md`), creating an unambiguous relationship between the source directory and the deployed command.

## Source Directory Structure

### Required: Source Layout

```
generate-knowledge-base/
  generate-knowledge-base.md     # Orchestrator command file
  Agents/                        # Subagent source directory (title case)
    spec-brainstormer.md
    spec-writer.md
    conventions-writer.md
    legacy-doc-consolidator.md
    adr-writer.md
    spec-auditor.md
    README.md
  README.md
```

### Observed: Title Case for `Agents/` Directory

The source directory for agent files uses title case (`Agents/`), while the deployment target uses lowercase (`.claude/agents/`). This is the only title-cased directory in the project. The deployment instructions use a direct `cp` command that handles the case difference. The reason for the title-case choice is not documented in the codebase; see Assumptions.

## Deployment Target Naming

### Required: Claude Code Deployment Paths

Files must be deployed to these exact paths in the target project:

| Source | Target |
|---|---|
| `generate-knowledge-base.md` | `.claude/commands/generate-knowledge-base.md` |
| `Agents/*.md` | `.claude/agents/*.md` |

The `.claude/commands/` and `.claude/agents/` paths are Claude Code platform conventions.

## Output Taxonomy Naming

### Required: Output Folder Names

The workflow creates this folder structure under `OUTPUT_ROOT` (default: `docs`):

```
{OUTPUT_ROOT}/
  architecture/
  architecture/decisions/
  conventions/
  specs/
  plans/
  reference/
  summary/
  summary/runs/
```

All folder names are lowercase, singular or plural as shown. These names are hardcoded in the orchestrator and must remain stable between runs.

### Required: Architecture Document Names

| File | Content |
|---|---|
| `architecture/overview.md` | System purpose, layers, major flows |
| `architecture/components.md` | Modules, responsibilities, dependency flow |
| `architecture/integrations.md` | External dependencies, services, databases |

### Required: Convention Document Names

| File | Content |
|---|---|
| `conventions/coding.md` | Layering, DI, error handling, async patterns |
| `conventions/testing.md` | Frameworks, placement, fixture patterns |
| `conventions/naming.md` | Namespaces, DTOs, components, interfaces |
| `conventions/api.md` | Route style, auth, versioning (created only when relevant) |

### Required: Spec Document Names

| File | Content |
|---|---|
| `specs/00-overview.md` | Product behavior and feature areas |

Additional spec files may be created when clearly supported by the codebase, but `00-overview.md` is always the first and primary spec document.

### Required: Reference Document Names

| File | Content |
|---|---|
| `reference/api.md` | API routes, auth, request/response patterns (created only when the project exposes or consumes meaningful APIs) |

### Required: ADR File Naming

ADR files follow this exact pattern:

```
architecture/decisions/NNNN-short-title-in-kebab-case.md
```

Where:
- `NNNN` is a zero-padded four-digit sequential number.
- The title portion uses kebab-case.
- Numbers are assigned sequentially from the highest existing file in the decisions folder.
- The ADR title inside the file uses Title Case: `# NNNN. Short Title in Title Case`.

**Example:** `architecture/decisions/0001-markdown-as-code-for-agent-definitions.md`

### Required: Run Summary Naming

| File | Pattern | Purpose |
|---|---|---|
| `summary/latest-run.md` | Fixed name | Most recent run summary, overwritten each run |
| `summary/runs/YYYYMMDD-HHMMSS.md` | Timestamp | Historical run summary, never overwritten |

The timestamp format `YYYYMMDD-HHMMSS` is explicitly required by the orchestrator -- it is described as "not advisory -- required for consistent history."

### Required: `.gitkeep` in Empty Directories

Empty output directories are tracked with a `.gitkeep` file. This is created in STEP 0 for all output directories that do not already contain files.

## YAML Frontmatter Naming

### Required: Description Field Style

The `description` field in both command and agent frontmatter uses a single sentence starting with a verb (present tense, third person implied or imperative):

| Component | `description` |
|---|---|
| Orchestrator | "Generates and maintains a project knowledge base for an existing software project" |
| spec-brainstormer | "Analyzes the repo and CLAUDE.md to understand purpose, layers, patterns, services, and integration points." |
| conventions-writer | "Extracts stable implementation conventions and project rules from the codebase and existing documentation." |

### Observed: Punctuation Inconsistency in Descriptions

Some agent descriptions end with a period, others do not. The orchestrator description has no trailing period. This is an inconsistency, not an intentional convention.

## PROJECT_TYPE Values

### Required: Project Type Identifiers

The orchestrator defines these exact string values for `PROJECT_TYPE`:

| Value | Meaning |
|---|---|
| `frontend` | React, Next, Angular, Vue, Nuxt, or Astro detected |
| `backend-dotnet` | .csproj, .sln, Program.cs, or Startup.cs detected |
| `backend-node` | Express, Fastify, Koa, NestJS, or Hapi detected |
| `mixed` | Both frontend and backend indicators present |

These values use kebab-case and are passed to agents as-is.

**Note on NestJS detection:** The `backend-node` detection searches for the string `nestjs` in `package.json` dependencies. Actual NestJS projects use `@nestjs/core` as the package name; the bare string `nestjs` does not appear in a typical `dependencies` block. This is a potential detection gap that may cause NestJS projects to be misclassified.

### Observed: No `tooling` or `unknown` Type

The current codebase being documented is itself a tooling project, but the PROJECT_TYPE detection logic does not include a `tooling` or `unknown` fallback. When none of the four detection rules match, the orchestrator does not set a default value — `PROJECT_TYPE` is left undefined and passed to agents as an empty or unset variable. This is an unhandled edge case that could cause subagent misbehavior in projects that do not match any known type.

## Assumptions

- The `Agents/` title-case directory name in the source tree has no documented rationale. It may be intentional for visual distinction or an incidental choice. The deployment target `.claude/agents/` uses lowercase per Claude Code conventions.
- The zero-padded four-digit ADR number (`NNNN`) implies a maximum of 9999 ADRs per project. This is assumed to be sufficient for all practical use cases.
- The `00-` prefix on `specs/00-overview.md` implies additional specs would use numeric prefixes for ordering (e.g., `01-`, `02-`), though only `00-overview.md` is explicitly required.
- The absence of a `tooling` or `unknown` PROJECT_TYPE is likely an intentional scoping decision -- the skill is designed for application codebases, not for documenting itself.
