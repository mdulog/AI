# Naming Conventions

This project is a pure-markdown Claude Code skill. Naming conventions apply to file names, folder names, YAML frontmatter identifiers, model declarations, and the naming patterns the orchestrator imposes on generated output in target projects.

These conventions distinguish **required patterns** (declared or enforced in the orchestrator/agent files) from **observed conventions** (recurring across files but not formally enforced).

## Agent File Naming

### Required: Kebab-Case Filenames Matching the `name` Field

Every agent file uses kebab-case for its filename, and the filename (without `.md`) **exactly matches** the `name` field in the file's YAML frontmatter.

| File | `name` field |
|---|---|
| `spec-brainstormer.md` | `spec-brainstormer` |
| `spec-writer.md` | `spec-writer` |
| `conventions-writer.md` | `conventions-writer` |
| `legacy-doc-consolidator.md` | `legacy-doc-consolidator` |
| `adr-writer.md` | `adr-writer` |
| `spec-auditor.md` | `spec-auditor` |

This alignment is load-bearing. The orchestrator's STEP 0 verification checks for files by path (`.claude/agents/{name}.md`), and the `Agent` tool invokes agents by their `name` field. A mismatch causes STEP 0 to halt with a "missing agent" error.

### Observed: Agent Name Pattern `{function}-{role}`

All six agents follow the `{function}-{role}` shape:

- The first segment names the primary function or domain: `spec`, `conventions`, `legacy-doc`, `adr`.
- The second segment names the agent's role: `brainstormer`, `writer`, `consolidator`, `auditor`.

This is consistent across the existing agents but not formally enforced. New agents should follow it for predictability.

## Command File Naming

### Required: Kebab-Case Slash Command

The orchestrator command file uses kebab-case: `generate-knowledge-base.md`. This becomes the slash-command name in Claude Code: `/generate-knowledge-base`.

The command filename matches the project directory name (`generate-knowledge-base/generate-knowledge-base.md`), creating an unambiguous relationship between the source directory and the deployed command.

## Source Directory Layout

### Required: Source Tree

```
generate-knowledge-base/
  generate-knowledge-base.md     # Orchestrator command file
  Agents/                        # Subagent source directory (title case — see below)
    spec-brainstormer.md
    spec-writer.md
    conventions-writer.md
    legacy-doc-consolidator.md
    adr-writer.md
    spec-auditor.md
    README.md
  README.md
```

### Observed: Title-Case `Agents/` Directory

The source directory for agent files uses title case (`Agents/`), while the deployment target uses lowercase (`.claude/agents/`). This is the only title-cased directory in the project. The deployment instructions use a direct `cp` command that handles the case difference. The reason for the title-case choice is not documented in the codebase.

## Deployment Target Naming

### Required: Claude Code Deployment Paths

Files must be deployed to these exact paths in the target project:

| Source | Target |
|---|---|
| `generate-knowledge-base.md` | `.claude/commands/generate-knowledge-base.md` |
| `Agents/*.md` | `.claude/agents/*.md` |

The `.claude/commands/` and `.claude/agents/` paths are Claude Code platform conventions, not project choices.

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

All folder names are lowercase, singular or plural as shown. These names are hardcoded in the orchestrator (§ Documentation structure) and must remain stable between runs.

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
| `conventions/api.md` | Route style, auth, versioning (created **only when relevant** — not generated for this project) |

### Required: Spec Document Names

| File | Content |
|---|---|
| `specs/00-overview.md` | Product behavior and feature areas (always required) |

Additional spec files may be created when clearly supported by the codebase. The numeric prefix on `00-overview.md` implies further specs would be ordered (`01-`, `02-`, ...), though only `00-overview.md` is mandatory.

### Required: Reference Document Names

| File | Content |
|---|---|
| `reference/api.md` | API routes, auth, request/response patterns (created **only when** the project exposes or consumes meaningful APIs) |

For this repository specifically, `reference/api.md` is intentionally not generated — the skill exposes no HTTP, RPC, or programmatic API.

### Required: ADR File Naming

ADR files follow this exact pattern:

```
architecture/decisions/NNNN-short-title-in-kebab-case.md
```

Where:

- `NNNN` is a **zero-padded four-digit** sequential number.
- The title portion uses **kebab-case**.
- Numbers are assigned sequentially from the highest existing file in the decisions folder, after a deduplication pass against existing topics (see `coding.md` § ADR Numbering is Centralized).
- The ADR title **inside the file** uses Title Case: `# NNNN. Short Title in Title Case`.

**Example:** `architecture/decisions/0001-markdown-as-code-for-agent-definitions.md`

This rule lives in `CLAUDE.md` (ADR Workflow section) and is enforced by `adr-writer`.

### Required: MADR Section Names (verbatim)

Every ADR file must use these exact section names, in this order, per `CLAUDE.md` and the orchestrator's MADR contract:

1. `# NNNN. Title`
2. `## Status`
3. `## Context and Problem Statement`
4. `## Considered Options`
5. `## Decision Outcome`
6. `## Consequences`
7. `## Assumptions` (project-specific addition; ends every generated doc)

Superseded ADRs update their `## Status` to `Superseded by NNNN` rather than being deleted (`CLAUDE.md` ADR Workflow).

### Required: Run Summary Naming

| File | Pattern | Purpose |
|---|---|---|
| `summary/latest-run.md` | Fixed name | Most recent run summary; overwritten each run |
| `summary/runs/YYYYMMDD-HHMMSS.md` | Timestamp | Historical run summary; never overwritten |

The timestamp format `YYYYMMDD-HHMMSS` is **required, not advisory** — the orchestrator declares it explicitly for consistent history. Use 24-hour time, no separators between fields, and a single hyphen between the date and time blocks (e.g. `20260508-143205.md`).

### Required: `.gitkeep` in Empty Output Directories

Empty output directories are tracked with a `.gitkeep` file. This is created in STEP 0 for any output directory that does not already contain files.

## Frontmatter Identifier Naming

### Required: Generic Model Aliases Only

The `model:` field in both command and agent frontmatter must use a **generic alias**, not a pinned version:

| Acceptable | Forbidden |
|---|---|
| `opus` | `claude-opus-4-6`, `claude-opus-4-7`, etc. |
| `sonnet` | `claude-sonnet-4-5`, etc. |
| `haiku` | `claude-haiku-3-5`, etc. |
| `inherit` | (any specific version) |

Rule source: `CLAUDE.md` § Model and Effort Policy and the orchestrator's § Model and effort policy — "Use generic aliases (`opus` / `sonnet` / `haiku` / `inherit`); never pin a specific version. Pins miss model improvements."

**Dev-tooling carve-out:** `scripts/smoke_grade.py` hardcodes `JUDGE_MODEL = "claude-opus-4-7"` (see the `JUDGE_MODEL` constant near the top of the script). The Anthropic Python SDK does not resolve generic aliases like `opus`, so dev tooling that calls the SDK directly must use exact model IDs. This carve-out is codified in `CLAUDE.md` § Model and Effort Policy. Bump the pin on model launches; do NOT propagate the pinned-version pattern into orchestrator or agent frontmatter.

### Required: `description` is a Single Verb-Led Sentence

The `description` field in both command and agent frontmatter is a single sentence starting with a verb (present tense, third person implied or imperative form):

| Component | `description` |
|---|---|
| Orchestrator | `Generates and maintains a project knowledge base for an existing software project` |
| `spec-brainstormer` | `Analyzes the repo and CLAUDE.md to understand purpose, layers, patterns, services, and integration points.` |
| `conventions-writer` | `Extracts stable implementation conventions and project rules from the codebase and existing documentation.` |

### Observed: Punctuation Inconsistency in `description`

`description` punctuation is inconsistent across files: 5 of 6 agents end with a period (`spec-brainstormer`, `conventions-writer`, `legacy-doc-consolidator`, `adr-writer`, `spec-auditor`); `spec-writer` and the orchestrator do not. Pick a single convention and apply it uniformly when reconciling — there is no enforcement primitive, so existing inconsistency must be resolved in a single sweep.

## PROJECT_TYPE Values

### Required: Project Type Identifiers

The orchestrator defines exactly these string values for `PROJECT_TYPE` (§ STEP 0 — Detect PROJECT_TYPE):

| Value | Meaning |
|---|---|
| `frontend` | React, Next, Angular, Vue, Nuxt, or Astro detected |
| `backend-dotnet` | `*.csproj`, `*.sln`, `Program.cs`, or `Startup.cs` detected |
| `backend-node` | Express, Fastify, Koa, NestJS, or Hapi detected |
| `mixed` | Both frontend and backend indicators present |

These values use kebab-case and are passed to subagents verbatim as inline prompt text.

### Observed: NestJS Detection Gap

The `backend-node` rule searches `package.json` for the bare string `nestjs`. Real NestJS projects depend on `@nestjs/core` instead — the bare string `nestjs` does not appear in a typical `dependencies` block. NestJS projects may therefore be misclassified. This is a known detection gap, not an intentional convention.

### Observed: No `tooling` or `unknown` Fallback

When none of the four detection rules match, the orchestrator does not assign a default value — `PROJECT_TYPE` is left undefined and passed to agents as an empty or unset variable. This repository (a tooling project) does not match any rule. The unhandled fallback is a known edge case, not a designed behavior.

## Assumptions

- The `Agents/` title-case directory has no documented rationale; it may be intentional for visual distinction or an incidental choice. The deployment target `.claude/agents/` uses lowercase per Claude Code conventions.
- The zero-padded four-digit `NNNN` ADR number implies a maximum of 9999 ADRs per project, which is assumed to be sufficient.
- The `00-` prefix on `specs/00-overview.md` implies subsequent specs would use numeric prefixes (`01-`, `02-`, ...) for ordering, though only `00-overview.md` is explicitly required.
- The `YYYYMMDD-HHMMSS` timestamp is assumed to be local time at the agent's host; the orchestrator does not specify a timezone explicitly.
- The absence of a `tooling`/`unknown` `PROJECT_TYPE` is treated as a known scoping limitation, not a deliberate design choice; the skill is intended for application codebases.
- Line numbers cited in this document reflect the orchestrator at generation time; they will drift as the file evolves.
