# Components

## Component Map

The system consists of one orchestrator and six subagents. Every component is a markdown file with YAML frontmatter declaring `name` (or `description` for the orchestrator), `tools` (or `allowed-tools`), and `model`. The Claude Code runtime interprets these declarations at invocation time and enforces tool boundaries.

```
Orchestrator (generate-knowledge-base/generate-knowledge-base.md)
  |
  |-- spec-brainstormer        [STEP 1]              read-only analysis
  |-- spec-writer              [STEP 2, STEP 4]      architecture + spec writing
  |-- conventions-writer       [STEP 3]              convention extraction
  |-- legacy-doc-consolidator  [STEP 0.6]            legacy doc merging
  |-- adr-writer               [STEP 5]              ADR creation + numbering
  |-- spec-auditor             [STEP 6]              read-only doc-vs-code audit
```

## Frontmatter Summary (verbatim)

The following table is the authoritative declaration set. Tool boundaries and model selection are enforced via these fields — there is no other configuration layer.

| Component | File | `name` | `tools` / `allowed-tools` | `model` |
|---|---|---|---|---|
| Orchestrator | `generate-knowledge-base/generate-knowledge-base.md` | n/a (slash-command) | `[Read, Write, Bash, Agent]` | `sonnet` |
| Brainstormer | `generate-knowledge-base/Agents/spec-brainstormer.md` | `spec-brainstormer` | `[Read, Bash, Glob, Grep]` | `opus` |
| Spec writer | `generate-knowledge-base/Agents/spec-writer.md` | `spec-writer` | `[Read, Write, Bash, Grep]` | `sonnet` |
| Conventions writer | `generate-knowledge-base/Agents/conventions-writer.md` | `conventions-writer` | `[Read, Write, Bash, Glob, Grep]` | `sonnet` |
| Legacy consolidator | `generate-knowledge-base/Agents/legacy-doc-consolidator.md` | `legacy-doc-consolidator` | `[Read, Write, Bash, Glob, Grep]` | `sonnet` |
| ADR writer | `generate-knowledge-base/Agents/adr-writer.md` | `adr-writer` | `[Read, Write, Bash, Glob]` | `opus` |
| Spec auditor | `generate-knowledge-base/Agents/spec-auditor.md` | `spec-auditor` | `[Read, Bash, Glob, Grep]` | `opus` |

Tool-shape boundaries enforced by these declarations:

- **Read-only agents** (`spec-brainstormer`, `spec-auditor`) lack `Write` — the runtime denies file modification, no prose enforcement needed.
- **Only the orchestrator declares `Agent`** — only the supervisor can dispatch subagents. The boundary is at the tool level (orchestrator frontmatter's `allowed-tools`).
- All writer agents have `Write` scoped to their target paths by *prose* convention; the tool itself accepts any path, so the orchestrator's invocation prompt and the agent's own instructions are what keep writes inside `OUTPUT_ROOT/`.

## Model and Effort Policy

Model selection is per-agent, declared once in the agent's frontmatter `model:` field — single source of truth. Reasoning effort is per-step, set by the orchestrator via `/effort <level>` immediately before each `Agent` dispatch. The full policy and rationale live in the orchestrator's § Model and effort policy and `CLAUDE.md` § Model and Effort Policy; do not duplicate it here.

Effort schedule actually used:

- `/effort medium` at session start; remains `medium` for STEPS 0–0.6, 2, 3, 4, 7, 8.
- `/effort high` before STEP 1 (`spec-brainstormer`), STEP 5 (`adr-writer`), STEP 6 (`spec-auditor`); reverted to `medium` after each.

The orchestrator does not add per-step `model` overrides on `Agent` invocations — model selection stays centralized in agent frontmatter to avoid drift.

## Orchestrator

**File:** `generate-knowledge-base/generate-knowledge-base.md`

**Frontmatter:**

```yaml
description: Generates and maintains a project knowledge base for an existing software project
allowed-tools: [Read, Write, Bash, Agent]
model: sonnet
```

**Responsibilities:**

- Controls all execution flow through the 12-step pipeline (STEPS 0, 0.4, 0.5, 0.6, 1, 2, 3, 4, 5, 6, 7, 8).
- Detects `PROJECT_TYPE` from repository markers (`frontend`, `backend-dotnet`, `backend-node`, `mixed`); halts on an ambiguous mixed result when no `OUTPUT_ROOT` argument is provided.
- Resolves `OUTPUT_ROOT` from `$ARGUMENTS` (default: `docs`) and `mode` from `$ARGUMENTS` (default: `full`).
- Verifies all six agent files are present in `.claude/agents/`; halts immediately if any are missing.
- Initializes `CLAUDE.md` via `/init` if absent; otherwise migrates legacy section references in place.
- Creates the output folder taxonomy and seeds empty folders with `.gitkeep`.
- Performs idempotency pre-flight via git-diff scoping (STEP 0.4) to skip unchanged steps on re-runs.
- Performs legacy doc migration (STEP 0.5) directly via `git mv` — this is filesystem moves only, not editorial work.
- Delegates analytical and writing work to subagents via the `Agent` tool.
- Issues `/effort high` before Opus-tier dispatches and `/effort medium` afterward.
- Confirms High/Medium audit corrections with the user before applying any (STEP 7).
- Writes the persistent run summary to `summary/latest-run.md` and a timestamped copy under `summary/runs/YYYYMMDD-HHMMSS.md`.
- Finalizes `CLAUDE.md` references (STEP 8).

**Boundaries:**

- Cannot perform STEPS 1, 2, 3, 4, 5, 6, or 0.6 in the main context — must delegate (orchestrator § Hard requirement).
- Cannot silently continue when a required agent is missing.

## spec-brainstormer

**File:** `generate-knowledge-base/Agents/spec-brainstormer.md`

**Step:** STEP 1 (always runs).

**Tool set:** `[Read, Bash, Glob, Grep]` — no `Write`. The agent cannot modify any file.

**Model:** `opus`. Effort `high` is set by the orchestrator before dispatch.

**Responsibilities:**

- Read `CLAUDE.md` and scan the full repository structure adapted to `PROJECT_TYPE`.
- Produce a structured analysis answering six questions: system purpose, major layers/components, patterns, external dependencies, HTTP-and-non-HTTP services, and inconsistencies/gaps.
- Self-check for contradictions, missing components, and pattern inconsistencies.
- Return a structured report inline (no file artifact). Later steps consume this report from the orchestrator's context.

**Internal parallelism:** allowed across independent top-level repo areas, provided the agent merges results into a single fan-in summary.

## spec-writer

**File:** `generate-knowledge-base/Agents/spec-writer.md`

**Steps:** STEP 2 (architecture + reference) and STEP 4 (specs) — invoked twice with different target sets.

**Tool set:** `[Read, Write, Bash, Grep]`.

**Model:** `sonnet`. Effort remains `medium` for both invocations.

**Responsibilities (STEP 2):**

- Generate or update `OUTPUT_ROOT/architecture/overview.md`, `OUTPUT_ROOT/architecture/components.md`, `OUTPUT_ROOT/architecture/integrations.md`.
- Generate or update `OUTPUT_ROOT/reference/api.md` *only* when the project exposes or consumes meaningful APIs.

**Responsibilities (STEP 4):**

- Generate or update `OUTPUT_ROOT/specs/00-overview.md`.
- Generate additional feature or domain specs only when clearly supported by the codebase or existing docs.
- Avoid duplicating architecture and conventions content; cross-reference instead.

**Boundaries:**

- Every generated file ends with `## Assumptions`.
- Only writes facts supported by the repo, existing docs, or the brainstorm report.
- Prefers incremental edits over complete rewrites when files already exist.

## conventions-writer

**File:** `generate-knowledge-base/Agents/conventions-writer.md`

**Step:** STEP 3 (always runs).

**Tool set:** `[Read, Write, Bash, Glob, Grep]`.

**Model:** `sonnet`. Effort `medium`.

**Responsibilities:**

- Generate or update `OUTPUT_ROOT/conventions/coding.md`, `testing.md`, `naming.md`, and `api.md` (the last only when relevant).
- Capture stable, repeatable rules already evident in the codebase; avoid one-off feature details.
- Distinguish required patterns from observed conventions when certainty is limited.
- Include concrete examples from the repo when useful.

## legacy-doc-consolidator

**File:** `generate-knowledge-base/Agents/legacy-doc-consolidator.md`

**Step:** STEP 0.6 (mode=full only).

**Tool set:** `[Read, Write, Bash, Glob, Grep]`.

**Model:** `sonnet`. Effort `medium`.

**Responsibilities:**

- Review legacy markdown files remaining after STEP 0.5 migration.
- Classify content by destination (`architecture/`, `conventions/`, `specs/`, `plans/`, `reference/`) and merge durable knowledge into the canonical doc set.
- Distill rather than copy verbatim; split mixed-concern legacy files across destination categories.
- Never delete legacy files automatically — preserve them until a human reviews.
- Produce a consolidation report listing reviewed files, updated canonical docs, and unresolved items.

**Note:** STEP 0.5 (filesystem migration) is performed by the orchestrator directly. STEP 0.6 (editorial consolidation) is the consolidator's exclusive scope. The two are deliberately split: the orchestrator handles `git mv`, the agent handles the editorial merge.

## adr-writer

**File:** `generate-knowledge-base/Agents/adr-writer.md`

**Step:** STEP 5 (mode=full only).

**Tool set:** `[Read, Write, Bash, Glob]` — note: no `Grep`. ADR work uses `Glob` to enumerate existing decisions and `Bash` for direct inspection.

**Model:** `opus`. Effort `high` is set by the orchestrator before dispatch.

**Responsibilities:**

- Read `OUTPUT_ROOT/architecture/overview.md`, related architecture docs, and the codebase.
- Identify 3–5 significant architectural decisions clearly evident in the implementation.
- Run a deduplication pass against existing ADRs (see below).
- Determine the next available `NNNN` number, assign sequential numbers to all new ADRs before writing any file, and produce MADR-format records.
- Refuse to invent decisions not supported by code or docs.

**Centralized ADR numbering and deduplication (load-bearing):**

ADR numbering is centralized in this single agent — never duplicated across parallel runs. Before assigning numbers, the agent:

1. Lists existing ADRs and their normalized topics (`adr-writer.md` — Deduplication procedure).
2. For each candidate decision, decides whether the topic is already covered by an existing ADR. If covered, it updates the existing ADR and does not assign a new number. If not covered, it states why before proceeding.
3. Only after every candidate has been evaluated against the existing topic list does it assign sequential numbers (`adr-writer.md` — Numbering procedure).

The orchestrator additionally runs `git pull` immediately before dispatching `adr-writer` (orchestrator § STEP 5) to ensure the local `decisions/` folder reflects the latest remote state. This is the project's only defense against ADR-number collisions when multiple developers run the workflow concurrently — parallel ADR creation is forbidden unless a single coordinator owns numbering (orchestrator § STEP 5).

## spec-auditor

**File:** `generate-knowledge-base/Agents/spec-auditor.md`

**Step:** STEP 6 (mode=full only).

**Tool set:** `[Read, Bash, Glob, Grep]` — no `Write`. The agent cannot modify any file; it returns a correction list for human approval.

**Model:** `opus`. Effort `high` is set by the orchestrator before dispatch.

**Responsibilities:**

- Audit all files under `OUTPUT_ROOT/architecture/`, `conventions/`, `specs/`, `reference/`, and `architecture/decisions/`.
- For each file, report: contradictions with real code, unverifiable assumptions, missing information, vague or generic content, and content that belongs in a different doc category.
- Produce prioritized corrections at High / Medium / Low.

**Internal parallelism:** allowed across independent per-file audits, provided the agent merges results into a single prioritized correction list as a fan-in summary.

The orchestrator (STEP 7) presents the High and Medium list to the user, takes confirmation, and applies only the confirmed subset. STEP 7 is intentionally orchestrator-direct — there is no separate "corrections-writer" agent.

## Step → Agent Mapping (authoritative)

| Step | Mode gate | Agent | Writes? | Notes |
|---|---|---|---|---|
| STEP 0 | always | (orchestrator) | yes | `CLAUDE.md`, folders |
| STEP 0.4 | skipped in `force` | (orchestrator) | no | git-diff scoping + manual edit detection |
| STEP 0.5 | full only | (orchestrator) | yes (moves only) | filesystem migration via `git mv` |
| STEP 0.6 | full only | `legacy-doc-consolidator` | yes | editorial consolidation |
| STEP 1 | always | `spec-brainstormer` | no | returns inline report |
| STEP 2 | always | `spec-writer` (1st) | yes | `architecture/`, `reference/api.md` (conditional) |
| STEP 3 | always | `conventions-writer` | yes | `conventions/` |
| STEP 4 | always | `spec-writer` (2nd) | yes | `specs/` |
| STEP 5 | full only | `adr-writer` | yes | `architecture/decisions/` |
| STEP 6 | full only | `spec-auditor` | no | returns prioritized correction list |
| STEP 7 | full only | (orchestrator) | yes | applies confirmed corrections |
| STEP 8 | always | (orchestrator) | yes | finalizes `CLAUDE.md`, writes run summary |

Light mode runs only STEP 0, 0.4, 1, 2, 3, 4, and 8.

## Communication Paths

There is no IPC, no queue, no shared in-memory state. All inter-component communication is one of:

- **Orchestrator → agent**: inline prompt content via the `Agent` tool. The orchestrator embeds the brainstorm report, target file list, `PROJECT_TYPE`, `OUTPUT_ROOT`, and step-specific instructions in the dispatch prompt.
- **Agent → orchestrator**: the agent's final assistant message, which the orchestrator reads as text. The orchestrator's dispatch prompts pass needed context inline (brainstorm report, target file list, `PROJECT_TYPE`, `OUTPUT_ROOT`); the prose convention is that agents return their report as a final message rather than as a side-channel `.md` file, but this is enforced by the dispatch prompt rather than the agent declaration.
- **Persistent state**: only the markdown files written under `OUTPUT_ROOT/` and the project-root `CLAUDE.md`. Subsequent runs read these as context.

## Dependency Flow

```
generate-knowledge-base.md
  |
  +-- depends on (must exist at runtime):
  |     .claude/agents/spec-brainstormer.md
  |     .claude/agents/spec-writer.md
  |     .claude/agents/conventions-writer.md
  |     .claude/agents/legacy-doc-consolidator.md
  |     .claude/agents/adr-writer.md
  |     .claude/agents/spec-auditor.md
  |
  +-- depends on (Claude Code harness):
  |     Agent, Read, Write, Bash, Glob, Grep tools
  |     /effort, /init slash commands (gracefully degraded)
  |
  +-- writes to:
        CLAUDE.md (target project root)
        OUTPUT_ROOT/ (entire docs tree)
```

Agents have no dependencies on each other at the file level — each is invoked independently with all needed context inline. The only ordering dependency is logical: STEP 1's brainstorm report is required input for STEPS 2, 3, 4, 5, and 6, and the orchestrator passes it along on each dispatch.

## Assumptions

- The frontmatter table reflects the current state of every agent file as of this run; if an agent's `tools` or `model` is later changed, the orchestrator's STEP 0 verification list must be updated too.
- Tool-set enforcement is strict at the runtime level — the harness denies `Write` to a read-only agent. This is the documented intent of the design but is observable only by attempting an unauthorized call.
- Write-path scoping (e.g. "spec-writer only writes under `OUTPUT_ROOT/architecture/` and `OUTPUT_ROOT/reference/`") is enforced by prose in the agent file and orchestrator dispatch — there is no path-level enforcement primitive in the harness.
- The orchestrator's 575-line count is from the version inspected at generation time; the count will drift as the file evolves.
- The skill assumes Claude Code resolves the generic model aliases at dispatch and never observes the resolved model version, so version drift is invisible to the workflow.
