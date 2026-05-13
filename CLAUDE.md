# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository is a **Claude Code skill** called `generate-knowledge-base`. It provides a multi-agent orchestration workflow that analyzes any software project and generates a structured knowledge base: architecture docs, conventions, specs, ADRs, and API references.

The skill is not a standalone application — it is deployed _into_ target projects as a Claude Code custom command (`/generate-knowledge-base`) and invoked from within those projects.

## Repository Structure

- `generate-knowledge-base/generate-knowledge-base.md` — The orchestrator skill definition. This is the main entry point, deployed to `.claude/commands/` in target projects. It defines a 12-step phase-based workflow (STEP 0 through STEP 8, including intermediate steps 0.4, 0.5, 0.6) that delegates analytical work to subagents.
- `generate-knowledge-base/Agents/*.md` — Six subagent definitions deployed to `.claude/agents/` in target projects. Each agent has a specific role in the workflow (see below).

## Architecture

- Architecture docs live in docs/architecture/
- Read docs/architecture/overview.md before making structural or architectural changes
- Read docs/architecture/components.md and docs/architecture/integrations.md when working in unfamiliar areas

The workflow is **supervisor-led and phase-based** — the orchestrator runs steps sequentially and delegates analytical/writing work to specialized subagents. No overlapping write operations run in parallel.

### Orchestrator Flow

```
STEP 0    Pre-flight (detect project type, verify agents, init/migrate CLAUDE.md, create folders)
STEP 0.4  Idempotency pre-flight (git-diff scoping, manual edit detection)
STEP 0.5  Migrate legacy doc layouts to new taxonomy (full mode only)
STEP 0.6  Consolidate legacy content into canonical docs (full mode only, uses legacy-doc-consolidator agent)
STEP 1    Brainstorm — deep codebase analysis via spec-brainstormer agent (read-only)
STEP 2    Architecture docs via spec-writer agent
STEP 3    Conventions docs via conventions-writer agent
STEP 4    Specs via spec-writer agent (second invocation, different target files)
STEP 5    ADRs via adr-writer agent (full mode only)
STEP 6    Audit all docs via spec-auditor agent (full mode only, read-only)
STEP 7    Apply user-confirmed corrections (full mode only)
STEP 8    Finalize CLAUDE.md in the target project
```

### Subagent Roles

| Agent | File | Steps | Writes files? |
|---|---|---|---|
| `spec-brainstormer` | `Agents/spec-brainstormer.md` | 1 | No — returns a structured analysis report |
| `spec-writer` | `Agents/spec-writer.md` | 2, 4 | Yes — architecture docs and specs |
| `conventions-writer` | `Agents/conventions-writer.md` | 3 | Yes — coding, testing, naming, API conventions |
| `legacy-doc-consolidator` | `Agents/legacy-doc-consolidator.md` | 0.6 | Yes — merges legacy docs into new taxonomy |
| `adr-writer` | `Agents/adr-writer.md` | 5 | Yes — MADR-format decision records |
| `spec-auditor` | `Agents/spec-auditor.md` | 6 | No — returns prioritized correction list |

### Key Design Decisions

- **Agents are markdown files with YAML frontmatter**, not code. Each declares `name`, `description`, and `tools` (the set of Claude Code tools the agent is allowed to use).
- **The orchestrator enforces agent boundaries** — brainstormer and auditor are read-only; writers are scoped to specific output paths.
- **Three execution modes** (`full`, `light`, `force`) control which steps run. Light mode skips legacy migration, ADRs, audit, and corrections.
- **Idempotency via git-diff scoping** (STEP 0.4) — on re-runs, the orchestrator uses `git log`/`git diff` to determine which steps actually need to re-execute based on what source files changed since the last docs commit.
- **Safe parallelism policy** — fan-out is allowed only within a step when tasks are independent and write to distinct files, with a mandatory fan-in summary before proceeding.
- **Model + effort follow a token-hygiene policy** — orchestrator on Sonnet/medium; subagents declare a model in frontmatter; orchestrator escalates effort to `high` only around `spec-brainstormer`, `adr-writer`, and `spec-auditor`. See § Model and Effort Policy.

## Model and Effort Policy

Two stacked rules govern token spend:

**Model rule.**
1. **Sonnet** is the default.
2. **Opus** is used only where escalation is justified by complexity, ambiguity, or compounding output quality.
3. **Haiku** is reserved for narrow mechanical chores — no current subagent qualifies.

**Effort ladder.**
1. **Sonnet + medium** — default for orchestration and standard generation.
2. **Sonnet + high** — try this before escalating model.
3. **Opus + high** — truly hard tasks (current Opus agents sit here).
4. **Opus + max** — rare, highest-stakes reasoning; no current step qualifies.
5. **Haiku + low** — narrow mechanical chores; no current step qualifies.

| Agent | Model | Effort | Why this cell |
|---|---|---|---|
| (orchestrator) | `sonnet` | `medium` | Procedural coordination, git-diff scoping, dispatch. |
| `spec-brainstormer` | `opus` | `high` | Output feeds every downstream writer; quality compounds. |
| `spec-writer` | `sonnet` | `medium` | Structured generation from a clear report. |
| `conventions-writer` | `sonnet` | `medium` | Bounded judgment with brainstorm in hand. |
| `legacy-doc-consolidator` | `sonnet` | `medium` | Editorial categorization with explicit rules. |
| `adr-writer` | `opus` | `high` | Deduplication and significance judgment; collisions are costly. |
| `spec-auditor` | `opus` | `high` | Contradiction detection gates the corrections step. |

Mechanics:
- **Model**: the agent's frontmatter `model:` is the single source of truth. Use generic aliases (`opus` / `sonnet` / `haiku` / `inherit`). Never pin a specific version (e.g. `claude-opus-4-6`) — pins miss model improvements. **Exception**: dev tooling under `scripts/` that calls the Anthropic SDK directly must use specific model IDs (e.g. `claude-opus-4-7`) because the SDK does not resolve aliases. This carve-out is scoped strictly to dev tooling — orchestrator and agent frontmatter must use generic aliases.
- **Effort**: set by the orchestrator via `/effort <level>` before each `Agent` dispatch. Default is `medium`; escalate to `high` around `spec-brainstormer`, `adr-writer`, `spec-auditor`, then revert.
- No per-step `model` overrides on `Agent` invocations.
- A new subagent added without a `model:` field will inherit the orchestrator's `sonnet` — a safe default.

## Output Taxonomy (generated in target projects)

```
docs/
  architecture/overview.md, components.md, integrations.md
  architecture/decisions/NNNN-*.md    (MADR-format ADRs)
  conventions/coding.md, testing.md, naming.md, api.md
  specs/00-overview.md
  reference/api.md
  plans/
  summary/latest-run.md, runs/YYYYMMDD-HHMMSS.md
```

## Deployment (how to install into a target project)

```bash
# From the target project root:
mkdir -p .claude/commands .claude/agents
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
# Then run: /generate-knowledge-base
```

## When Modifying This Project

- The orchestrator (`generate-knowledge-base.md`) is the source of truth for step ordering, agent delegation rules, mode behavior, and safety policies. Agent files must stay consistent with what the orchestrator expects.
- Agent frontmatter (`name`, `description`, `tools`) must match how the orchestrator invokes them. If you rename an agent or change its tool set, update the orchestrator's verification list in STEP 0 and the corresponding invocation.
- ADR numbering is centralized in `adr-writer` with a deduplication procedure — this is intentional to prevent collisions. Do not add parallel ADR creation without a numbering coordinator.
- The safe parallelism policy in the orchestrator is load-bearing — relaxing it risks file corruption when multiple agents write overlapping targets.

## Conventions

- Conventions live in docs/conventions/
- Read the relevant convention files before generating or modifying code
- Treat convention documents as project rules unless the user explicitly overrides them

## Specs

- Specs live in docs/specs/
- Read the relevant spec before implementing a feature or behavior change
- Treat specs as feature intent, not as authority over architecture or conventions

## ADR Workflow

- ADRs live in docs/architecture/decisions/
- Before any architectural decision, read all existing files in docs/architecture/decisions/
- Name ADR files: NNNN-short-title-in-kebab-case.md
- Auto-increment the number based on the highest existing file in docs/architecture/decisions/
- Use MADR format: Title, Status, Context and Problem Statement, Considered Options, Decision Outcome, Consequences
- If superseding an ADR, update the old ADR status to `Superseded by NNNN`

## Documentation

- Read docs/architecture/overview.md before starting major work
- Read docs/architecture/components.md and docs/architecture/integrations.md when working in unfamiliar areas
- Read docs/conventions/ before generating or modifying code
- Read the relevant files in docs/specs/ when implementing features
- Read existing ADRs in docs/architecture/decisions/ before proposing structural changes
- Add new ADRs for significant architectural decisions
