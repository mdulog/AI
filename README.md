# generate-knowledge-base

Generate a living knowledge base for any software project in a single Claude Code command.

## What it does

When you join a new codebase, you spend days building a mental model that experienced team members carry in their heads — what the system does, how the layers fit together, what patterns are followed, and why key decisions were made. That knowledge is rarely written down, and when it is, it drifts out of sync with the code.

`generate-knowledge-base` runs a structured, multi-agent analysis of your codebase and produces a complete, evidence-based knowledge base: architecture docs, coding conventions, product specs, architectural decision records, and an API reference. Re-run it as the codebase evolves — it updates docs in place rather than rewriting from scratch.

## Quick start

```bash
# 1. Deploy the orchestrator to your project
mkdir -p .claude/commands
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/

# 2. Deploy the agents
mkdir -p .claude/agents
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/

# 3. Run from your project root in Claude Code
/generate-knowledge-base
```

Docs are written to `docs/` by default. Pass a custom folder as the first argument:

```bash
/generate-knowledge-base my-docs
```

## What gets generated

| Output | Path | Purpose |
|---|---|---|
| Architecture overview | `docs/architecture/overview.md` | System purpose, layers, major flows |
| Components | `docs/architecture/components.md` | Modules, responsibilities, dependency flow |
| Integrations | `docs/architecture/integrations.md` | Databases, queues, external APIs, services |
| API reference | `docs/reference/api.md` | Routes, auth, request/response patterns (when applicable) |
| Coding conventions | `docs/conventions/coding.md` | Layering, error handling, async patterns |
| Testing conventions | `docs/conventions/testing.md` | Frameworks, test placement, fixture patterns |
| Naming conventions | `docs/conventions/naming.md` | Namespaces, DTOs, components, interfaces |
| Specs overview | `docs/specs/00-overview.md` | Product behavior and feature areas |
| ADRs | `docs/architecture/decisions/NNNN-*.md` | MADR-format architectural decision records |

## Execution modes

| Mode | What runs |
|---|---|
| `mode=full` (default) | Complete workflow: brainstorm, all doc generation, legacy migration, ADRs, audit, corrections, CLAUDE.md finalization |
| `mode=light` | Essential steps only: brainstorm, architecture docs, conventions, specs, CLAUDE.md finalization |
| `mode=force` | Same as `full` but skips git-diff scoping and uncommitted-change confirmation |

```bash
/generate-knowledge-base docs mode=light
/generate-knowledge-base docs mode=force
```

Use `mode=light` for a quick refresh. Use `mode=force` when the docs folder is out of sync with git.

## Supported project types

The workflow auto-detects your stack:

| Type | Detected from |
|---|---|
| `frontend` | `package.json` with React, Next, Angular, Vue, Nuxt, or Astro |
| `backend-dotnet` | `*.csproj`, `*.sln`, `Program.cs`, or `Startup.cs` |
| `backend-node` | `package.json` with Express, Fastify, Koa, NestJS, or Hapi |
| `mixed` | Both frontend and backend indicators present |

For `mixed` projects, pass an explicit output root or run from within the specific app subdirectory.

## How it works

The orchestrator runs a 12-step pipeline, delegating analytical and writing work to six specialized subagents. Steps execute strictly sequentially — no overlapping writes.

```
STEP 0    Pre-flight: detect project type, verify agents, init CLAUDE.md, create folders
STEP 0.4  Idempotency: git-diff scoping + manual edit detection
STEP 0.5  Migrate legacy doc layouts to new taxonomy (full mode only)
STEP 0.6  Consolidate legacy content into canonical docs (full mode only)
STEP 1    Brainstorm: deep codebase analysis via spec-brainstormer (read-only)
STEP 2    Architecture docs via spec-writer
STEP 3    Conventions docs via conventions-writer
STEP 4    Specs via spec-writer (second invocation)
STEP 5    ADRs via adr-writer (full mode only)
STEP 6    Audit all docs via spec-auditor (full mode only, read-only)
STEP 7    Apply corrections after user review (full mode only)
STEP 8    Finalize CLAUDE.md
```

Each agent is a markdown file with YAML frontmatter — no compiled code. See [`generate-knowledge-base/Agents/README.md`](generate-knowledge-base/Agents/README.md) for what each agent does.

## CLAUDE.md integration

After a run, your project's `CLAUDE.md` is updated so Claude Code automatically loads the right context before making changes:

```markdown
## Architecture
- Read docs/architecture/overview.md before making structural changes

## Conventions
- Read docs/conventions/ before generating or modifying code

## ADR Workflow
- ADRs live in docs/architecture/decisions/
- Name files: NNNN-short-title-in-kebab-case.md
```

## Re-running

On subsequent runs the workflow uses `git log`/`git diff` to detect what changed since the last docs commit and skips unchanged steps. Commit the output after each run to establish the baseline:

```bash
git add docs/ CLAUDE.md
git commit -m "docs: update knowledge base"
```

## Repository structure

```
generate-knowledge-base/
  generate-knowledge-base.md   Orchestrator (deploy to .claude/commands/)
  Agents/
    spec-brainstormer.md       Read-only codebase analyzer (STEP 1)
    spec-writer.md             Architecture + spec writer (STEPS 2, 4)
    conventions-writer.md      Convention extractor (STEP 3)
    legacy-doc-consolidator.md Legacy doc merger (STEP 0.6)
    adr-writer.md              ADR writer with deduplication (STEP 5)
    spec-auditor.md            Read-only doc auditor (STEP 6)
    README.md                  Agent documentation
  README.md                    Detailed usage and troubleshooting
docs/                          Generated knowledge base (this repo documents itself)
```

## Troubleshooting

**`/generate-knowledge-base` command not found**
The orchestrator isn't deployed. Copy `generate-knowledge-base.md` to `.claude/commands/` in your target project.

**"Agent X is missing" at startup**
Copy all files from `Agents/` to `.claude/agents/` in your target project. The orchestrator hard-stops with the exact missing path.

**`reference/api.md` wasn't generated**
Only created when the project exposes or consumes meaningful APIs. Expected for projects with no API layer.

**ADRs describe decisions I don't agree with**
The `adr-writer` only records decisions evident in the code. If an ADR seems off, the underlying code pattern may be inconsistent — the ADR is surfacing a real signal.

## License

GPL-3.0
