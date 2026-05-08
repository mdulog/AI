# Architecture Overview

## System Purpose

`generate-knowledge-base` is a Claude Code skill that provides a multi-agent orchestration workflow for generating structured project documentation. It is not a standalone application -- it is deployed _into_ target projects as a Claude Code custom command (`/generate-knowledge-base`) and invoked from within those projects.

Given any software repository, the skill performs a deep codebase analysis and produces a complete knowledge base: architecture docs, coding conventions, product specs, architectural decision records (ADRs), and an API reference. The output is designed to be re-run as the codebase evolves, keeping documentation current through incremental updates rather than full rewrites.

## Architectural Style

The system follows a **supervisor-led, phase-based orchestration** pattern:

- A single orchestrator controls all execution flow.
- Six specialized subagents perform the analytical and writing work.
- Steps execute strictly sequentially -- no overlapping write operations run in parallel.
- The orchestrator delegates to subagents via the Claude Code `Agent` tool, passing context (brainstorm reports, project type, output root) as inline prompt content rather than file artifacts.

This is a **prompt-engineering architecture**, not a compiled software system. Every component is a markdown file with YAML frontmatter that declares the agent's identity, description, and permitted tool set. The Claude Code runtime interprets these files and enforces tool boundaries.

## Execution Flow

The orchestrator defines a 12-step pipeline (STEP 0 through STEP 8, including intermediate steps 0.4, 0.5, and 0.6):

```
STEP 0    Pre-flight
            - Detect PROJECT_TYPE from repo markers
            - Verify all 6 agent files exist in .claude/agents/
            - Initialize or migrate CLAUDE.md
            - Create output folder structure

STEP 0.4  Idempotency pre-flight
            - Git-diff scoping: determine which steps need re-execution
            - Manual edit detection: warn about uncommitted doc changes

STEP 0.5  Legacy doc migration (full mode only)
            - Move legacy files to new taxonomy paths via git mv

STEP 0.6  Legacy doc consolidation (full mode only)
            - Editorial pass: classify and merge legacy content into canonical docs
            - Delegated to legacy-doc-consolidator agent

STEP 1    Brainstorm (read-only)
            - Deep codebase analysis via spec-brainstormer agent
            - Produces a structured report consumed by later steps

STEP 2    Architecture docs
            - spec-writer agent generates overview, components, integrations
            - Also generates reference/api.md when the project has APIs

STEP 3    Conventions docs
            - conventions-writer agent extracts coding, testing, naming, API conventions

STEP 4    Specs
            - spec-writer agent (second invocation) generates product/feature specs

STEP 5    ADRs (full mode only)
            - adr-writer agent identifies 3-5 architectural decisions, writes MADR files

STEP 6    Audit (full mode only, read-only)
            - spec-auditor agent reviews all docs against codebase
            - Produces prioritized correction list (High / Medium / Low)

STEP 7    Apply corrections (full mode only)
            - User reviews and confirms corrections before any edits are made

STEP 8    Finalize CLAUDE.md
            - Update target project's CLAUDE.md with references to generated docs
```

### Data Flow Between Steps

The brainstorm report from STEP 1 is the primary analytical artifact. It is passed as inline context in Agent invocations to STEP 2, STEP 3, and STEP 4 -- it is not written to a file. Each subsequent writing step receives this report plus access to the codebase and any existing docs under the output root.

The audit report from STEP 6 flows into STEP 7, where the orchestrator presents corrections to the user before applying them.

## Execution Modes

Three modes control which steps run:

| Mode | Behavior |
|---|---|
| `full` (default) | Runs all steps: migration, consolidation, brainstorm, all doc generation, ADRs, audit, corrections, finalization |
| `light` | Runs only essential steps: STEP 0, 0.4, 1, 2, 3, 4, 8. Skips migration, consolidation, ADRs, audit, and corrections |
| `force` | Identical to `full` but bypasses STEP 0.4 git-diff scoping and manual edit confirmation. Use when docs are out of sync with git |

The mode is passed via `$ARGUMENTS` (e.g., `mode=light`). If unspecified, `full` is used.

## Deployment Model

The skill is deployed by copying files into the target project:

```
Target project/
  .claude/
    commands/
      generate-knowledge-base.md    <-- orchestrator
    agents/
      spec-brainstormer.md          <-- 6 subagent files
      spec-writer.md
      conventions-writer.md
      legacy-doc-consolidator.md
      adr-writer.md
      spec-auditor.md
```

The orchestrator runs within the Claude Code runtime on the user's machine. It requires:

- **Claude Code** as the execution environment (provides the `Read`, `Write`, `Bash`, `Agent`, `Glob`, `Grep` tools). Note: the orchestrator itself only declares `[Read, Write, Bash, Agent]` — it uses `Bash` for file-discovery operations rather than `Glob` or `Grep` directly.
- **Opus 4.6 model** (declared in the orchestrator's frontmatter via `model: claude-opus-4-6`)
- **Git** (optional; used for idempotency scoping and legacy migration, degrades gracefully if unavailable)

## Output Taxonomy

The workflow produces this folder structure in the target project:

```
{OUTPUT_ROOT}/
  architecture/
    overview.md              System purpose, layers, major flows
    components.md            Modules, responsibilities, dependency flow
    integrations.md          External dependencies, services, databases
    decisions/
      NNNN-*.md              MADR-format architectural decision records
  conventions/
    coding.md                Layering, DI, error handling, async patterns
    testing.md               Frameworks, placement, fixture patterns
    naming.md                Namespaces, DTOs, components, interfaces
    api.md                   Route style, auth, versioning (when relevant)
  specs/
    00-overview.md           Product behavior and feature areas
  reference/
    api.md                   API routes, auth, request/response (when relevant)
  plans/                     (created by STEP 0; populated only by legacy-doc-consolidator when legacy content is classified as "plan" — not written to by standard pipeline agents)
  summary/
    latest-run.md            Most recent run summary
    runs/
      YYYYMMDD-HHMMSS.md    Timestamped historical run summaries
```

The default `OUTPUT_ROOT` is `docs`. Users can override it via `$ARGUMENTS`.

## Important Constraints

### Idempotency

On re-runs, STEP 0.4 uses `git log` and `git diff` to determine what source files changed since the last documentation commit. Steps are skipped when their inputs have not changed:

- If only docs changed (no source code changes): only STEP 8 runs.
- If source code changed: STEPS 1-5 + 8 run (plus 6 and 7 in full mode).
- If nothing changed: the user is prompted to force re-run or exit.

### Safe Parallelism

Fan-out within a step is allowed only when all parallel tasks work on independent inputs, write to distinct files, and produce an explicit fan-in summary before downstream work continues. Writes to the same file, CLAUDE.md operations, and ADR numbering must never be parallelized without a centralized coordinator.

### Human-in-the-Loop

STEP 7 is the only step that requires user confirmation before modifying files. The orchestrator presents the audit's High and Medium corrections and waits for the user to approve before applying edits.

### Agent Enforcement

The orchestrator hard-stops if any required agent file is missing from `.claude/agents/`. It does not silently fall back to performing the work in the main context. This is an intentional safety boundary -- each agent has a scoped tool set and role, and bypassing agents would remove those constraints.

## Assumptions

- The Claude Code runtime is the only supported execution environment. The skill cannot run outside of Claude Code.
- The `model: claude-opus-4-6` declaration in the orchestrator frontmatter is honored by the Claude Code runtime to select the model for the orchestrator thread. Subagent model selection is assumed to inherit from the orchestrator or follow Claude Code defaults.
- Git is expected but not required. When git is unavailable, idempotency scoping (STEP 0.4) and legacy migration via `git mv` (STEP 0.5) degrade gracefully.
- The `Agent` tool in Claude Code supports passing inline context (the brainstorm report) in the invocation prompt. The architecture relies on this capability for inter-step data flow.
- The Superpowers plugin integration is optional and opportunistic. Detection is orchestrator-side (via `.claude/skills/superpowers` or `settings.json`); no subagent declares a dependency on it. See `integrations.md` for the full detection and capability scope.
