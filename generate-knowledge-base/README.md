# generate-knowledge-base

Generate a living knowledge base for any software project in a single command.

## Why?

When you join a new codebase, you spend days building a mental model that experienced team members already carry in their heads — what the system does, how the layers fit together, what patterns are followed, and why key decisions were made. That knowledge is rarely written down, and when it is, it drifts out of sync with the code.

`generate-knowledge-base` runs a structured, multi-agent analysis of your codebase and produces a complete, evidence-based knowledge base: architecture docs, conventions, specs, ADRs, and an API reference. Re-run it to keep the docs current as the codebase evolves.

## Quick start

```bash
# 1. Deploy the orchestrator to your project
mkdir -p .claude/commands
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/

# 2. Deploy the agents to your project
mkdir -p .claude/agents
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/

# 3. Run from your project root in Claude Code
/generate-knowledge-base
```

That's it. Docs are written to `docs/` by default. A run summary lands in `docs/summary/latest-run.md`.

## What gets generated

| Output | Path | Purpose |
|---|---|---|
| Architecture overview | `docs/architecture/overview.md` | System purpose, layers, major flows |
| Components | `docs/architecture/components.md` | Modules, responsibilities, dependency flow |
| Integrations | `docs/architecture/integrations.md` | Databases, queues, external APIs, services |
| API reference | `docs/reference/api.md` | Routes, auth, request/response patterns |
| Coding conventions | `docs/conventions/coding.md` | Layering, error handling, DI, async patterns |
| Testing conventions | `docs/conventions/testing.md` | Frameworks, test placement, fixture patterns |
| Naming conventions | `docs/conventions/naming.md` | Namespaces, DTOs, components, interfaces |
| Specs overview | `docs/specs/00-overview.md` | Product behavior and feature areas |
| ADRs | `docs/architecture/decisions/` | MADR-format architectural decision records |
| Run summary | `docs/summary/latest-run.md` | What ran, what was created, gaps to review |

## Arguments

```bash
# Custom output folder
/generate-knowledge-base my-docs

# Light mode — skips legacy migration, consolidation, ADRs, audit, and corrections
/generate-knowledge-base docs mode=light

# Custom folder + light mode
/generate-knowledge-base my-docs mode=light

# Force mode — bypasses git-diff scoping and manual edit confirmation, runs all steps
/generate-knowledge-base docs mode=force
```

**`mode=full`** (default) runs the complete workflow: pre-flight, brainstorm, architecture docs, conventions, specs, legacy migration and consolidation, ADR generation, audit, correction, and `CLAUDE.md` finalization.

**`mode=light`** runs only the essential steps: pre-flight, brainstorm, architecture docs, conventions, specs, and `CLAUDE.md` finalization. Good for a quick refresh when you don't need ADRs or an audit pass.

**`mode=force`** is identical to `mode=full` but bypasses the STEP 0.4 git-diff scoping and uncommitted-change confirmation. Use when the docs folder is out of sync with git — for example, if a previous run completed but the output was never committed.

## Requirements

### Agent deployment

The six subagent files in `Agents/` must be present in `.claude/agents/` inside your **target project** before you run the workflow. The orchestrator hard-stops if any are missing and tells you exactly which file is absent.

```bash
# From your target project root
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
```

### Supported project types

The workflow auto-detects your stack from repository files:

| Detected type | Trigger |
|---|---|
| `frontend` | `package.json` with React, Next, Angular, Vue, Nuxt, or Astro |
| `backend-dotnet` | `*.csproj`, `*.sln`, `Program.cs`, or `Startup.cs` |
| `backend-node` | `package.json` with Express, Fastify, Koa, NestJS, or Hapi |
| `mixed` | Both frontend and backend indicators present |

For `mixed` projects, pass an explicit output root to scope the run to one app, or run from within the app subdirectory.

## How it works

The orchestrator runs eight ordered steps, delegating the analytical work to six specialised subagents. Each step must complete before the next begins — the workflow is phase-based, not parallel.

```
STEP 0   — Pre-flight: detect project type, verify agents, migrate CLAUDE.md, create folders
STEP 0.4 — Idempotency pre-flight: git-diff scoping + manual edit detection (skipped in force mode)
STEP 0.5 — Migrate legacy docs to the new folder structure (full mode only)
STEP 0.6 — Consolidate legacy content into canonical docs (full mode only)
STEP 1   — Brainstorm: deep codebase analysis → structured report
STEP 2   — Architecture docs: overview, components, integrations, API reference
STEP 3   — Conventions: coding, testing, naming, API conventions
STEP 4   — Specs: product behavior and feature area docs
STEP 5   — ADRs: 3–5 significant architectural decisions (full mode only)
STEP 6   — Audit: review all docs against real code, produce prioritised corrections (full mode only)
STEP 7   — Apply corrections: High and Medium issues fixed after user review (full mode only)
STEP 8   — Finalize CLAUDE.md: update doc references to reflect new taxonomy
```

See [`Agents/README.md`](Agents/README.md) for what each subagent does.

## CLAUDE.md integration

After the workflow runs, your `CLAUDE.md` is updated with references to the generated docs so that Claude Code automatically reads the right context before making changes. The sections added look like this:

```markdown
## Architecture
- Read docs/architecture/overview.md before making structural changes

## Conventions
- Read docs/conventions/ before generating or modifying code

## ADR Workflow
- ADRs live in docs/architecture/decisions/
- Name files: NNNN-short-title-in-kebab-case.md
```

## Re-running the workflow

The workflow is designed to be run repeatedly. On subsequent runs it:

- **Updates docs in place** rather than rewriting from scratch
- **Preserves existing content** that is still accurate
- **Migrates legacy paths** if you reorganised your docs folder between runs
- **Appends a timestamped run summary** to `docs/summary/runs/`

Commit the output after each run to capture a historical baseline:

```bash
git add docs/ CLAUDE.md
git commit -m "docs: update knowledge base"
```

## Troubleshooting

**`/generate-knowledge-base` command not found**
The orchestrator hasn't been deployed to your target project. Run:
```bash
mkdir -p .claude/commands
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/
```

**"Agent X is missing" at startup**
The agent files haven't been copied to `.claude/agents/` in your target project. Run:
```bash
mkdir -p .claude/agents
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
```

**"PROJECT_TYPE = mixed" and the workflow stopped**
You have both frontend and backend indicators at the root. Either run from within the specific app directory or pass an explicit output root:
```bash
/generate-knowledge-base apps/api/docs
```

**The workflow ran but `reference/api.md` wasn't generated**
`reference/api.md` is only created when the project exposes or consumes meaningful APIs. For pure frontend apps with no API layer of their own, this is expected.

**Some ADRs describe decisions I don't agree with**
The `adr-writer` agent only records decisions clearly evident in the code — it doesn't invent rationale. If an ADR seems off, the underlying code pattern may be inconsistent. The ADR is surfacing a real signal worth investigating.

**Docs are accurate but I want to capture more detail**
Run in `mode=full` if you ran `mode=light`, then review the audit output in STEP 6. The auditor will flag missing information as Medium or Low priority corrections.
