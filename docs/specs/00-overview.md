# Product Behavior Overview

This document describes what `generate-knowledge-base` does from the user's perspective. For the sibling `generate-prd` skill, see [`generate-prd/README.md`](../../generate-prd/README.md) and the design spec at [`2026-05-15-generate-prd-design.md`](./2026-05-15-generate-prd-design.md). This document covers `generate-knowledge-base` only.: the public command surface, the workflows a user actually runs, the files that appear in their project as a result, the prompts they will see, and the guarantees the skill makes about safety and idempotency.

For structural details (orchestrator internals, agent topology, parallelism rules), see [`architecture/overview.md`](../architecture/overview.md) and [`architecture/components.md`](../architecture/components.md). For the conventions enforced on generated docs, see [`conventions/`](../conventions/).

## Product Purpose

Most repositories accumulate institutional knowledge unevenly: some of it sits in code, some in scattered READMEs, some only in contributors' heads. `generate-knowledge-base` produces and maintains a single, structured knowledge base under `docs/` that:

- captures what the system is and how its parts fit together (architecture)
- captures the rules a contributor must follow when changing it (conventions)
- captures the externally visible product behavior (specs)
- records significant past decisions and their context (ADRs)
- documents APIs and other lookup surfaces when applicable (reference)

The intent is to compress onboarding time and make the project's CLAUDE.md context-aware: after a run, Claude Code in the target project automatically reads the right docs before making changes, because the orchestrator wires those references into `CLAUDE.md` (see orchestrator § STEP 8).

The skill is content-only — it does not generate code, run tests, push commits, or deploy anything. See [Out of Scope](#out-of-scope) for the explicit boundary.

## Public Surface

The skill is invoked through a single Claude Code custom slash command in the target project:

```
/generate-knowledge-base [output-root] [mode=full|light|force]
```

Both arguments are optional. They are parsed from `$ARGUMENTS` by pattern match (orchestrator § Arguments and § Execution mode), not by a formal argument parser:

| Argument | Default | Meaning |
|---|---|---|
| `output-root` | `docs` | Folder under the project root where all generated docs are written. |
| `mode=...` | `full` | Workflow execution mode — see [Execution Modes](#execution-modes). |

Examples:

```
/generate-knowledge-base
/generate-knowledge-base docs mode=light
/generate-knowledge-base apps/api/docs
/generate-knowledge-base mode=force
```

There is no programmatic, HTTP, or library entry point. The slash command IS the product surface.

## Execution Modes

Three modes select which steps run. The mode-permitted step set is intersected with STEP 0.4's git-diff scoping (see [Idempotency](#idempotency-and-re-runs)) — the more restrictive wins.

### Full Mode (default)

Runs every step: pre-flight, idempotency check, legacy migration, legacy consolidation, brainstorm, architecture, conventions, specs, ADRs, audit, correction, CLAUDE.md finalization, and run summary. Use it for first-time onboarding, after substantial codebase changes, or when a thorough refresh is needed.

### Light Mode

Runs the essentials and skips everything that is either historical (legacy doc handling) or human-in-the-loop (audit and corrections). Specifically skipped (per each step's skip clause in the orchestrator — § STEP 0.5, § STEP 0.6, § STEP 5, § STEP 6, § STEP 7):

- STEP 0.5 — legacy doc migration
- STEP 0.6 — legacy doc consolidation
- STEP 5 — ADR creation
- STEP 6 — audit
- STEP 7 — correction application

Always-on steps in light mode: STEP 0, STEP 0.4, STEP 1, STEP 2, STEP 3, STEP 4, STEP 8 (orchestrator § Execution mode). Each individual skipped step can be force-run by an explicit user request.

### Force Mode

Runs the same step set as full mode, but bypasses the STEP 0.4 git-diff scoping and the uncommitted-edit confirmation entirely (orchestrator § Execution mode). Use it when the docs folder has drifted from git — for example, when a previous run completed but the output was never committed.

## User-Facing Workflows

### First Run on a Fresh Project

1. Copy the skill files into `.claude/commands/` and `.claude/agents/` (one-time, see [Deployment](#deployment-model)).
2. Invoke `/generate-knowledge-base` from the target project root.
3. Pre-flight detects `PROJECT_TYPE`, verifies all six agent files, and either runs `/init` to create `CLAUDE.md` or migrates the existing one to the new taxonomy (orchestrator § STEP 0 — Check and migrate CLAUDE.md).
4. STEP 0.4 finds no prior docs commit and skips git-diff scoping; all subsequent steps proceed (orchestrator § STEP 0.4 — Step scoping via git diff).
5. STEPS 1-8 run end to end. The brainstorm report is built first; architecture, conventions, specs, and ADRs are written in sequence; the audit produces a correction list; the user confirms which corrections to apply; CLAUDE.md is finalized; a run summary is persisted.

Expected output: a populated `docs/` tree (see [Output Contract](#output-contract)) and an updated `CLAUDE.md` referencing it.

### Re-Run with No Source Changes

When the user re-runs the skill and the codebase has not changed since the last docs commit:

1. STEP 0.4 captures the last docs SHA and runs `git diff $LAST_SHA HEAD --name-only` (orchestrator § STEP 0.4 — Step scoping via git diff).
2. With no source changes detected, the orchestrator prompts: *"no changes detected since last run — Force re-run? [y/N]"* (orchestrator § STEP 0.4 — Step scoping via git diff).
3. **N** — exit immediately. Docs are untouched.
4. **Y** — run all steps unconditionally.

If only files inside `OUTPUT_ROOT/` changed, STEP 8 runs alone (orchestrator § STEP 0.4 — Step scoping via git diff) — just CLAUDE.md is reconciled against the existing docs.

### Re-Run with Source Changes

When source files outside `OUTPUT_ROOT/` have changed since the last docs commit, STEP 0.4 selects "STEPS 1-5 + 8" (plus 0.5, 0.6, 6, and 7 when in full mode — orchestrator § STEP 0.4 — Step scoping via git diff). The orchestrator reports the inferred step set before proceeding so the user can see what will actually re-run.

### Recovery via Force Mode

When the docs folder has been hand-edited or generated outside of git, STEP 0.4's git-diff scoping is misleading. `mode=force` bypasses both checks (orchestrator § Execution mode) and runs the full pipeline unconditionally. Use this after manual cleanup or when restoring from a non-git source.

## Output Contract

After a successful run, the user can expect this layout under `OUTPUT_ROOT/` (orchestrator § Documentation structure and § Documentation intent):

| Path | Purpose |
|---|---|
| `architecture/overview.md` | System purpose, architectural style, major flows, deployment shape. |
| `architecture/components.md` | Major modules, responsibilities, dependency boundaries. |
| `architecture/integrations.md` | External services, databases, queues, schedulers, auth. |
| `architecture/decisions/NNNN-*.md` | MADR-format ADRs (full mode only). |
| `conventions/coding.md` | Coding standards verifiable in the repo. |
| `conventions/testing.md` | Testing conventions and structure. |
| `conventions/naming.md` | Naming and casing rules. |
| `conventions/api.md` | API conventions — generated **only** when the codebase has an API surface (HTTP routes, GraphQL, gRPC, public library exports, or consumed-API clients). Not created as a stub when absent. |
| `specs/00-overview.md` | Product behavior overview (this document). |
| `specs/*.md` | Additional feature specs (only when clearly supported by the codebase). |
| `reference/api.md` | API reference — generated **only** when the codebase has an API surface per the same markers as `conventions/api.md`. Not created as a stub when absent; the folder is tracked by `.gitkeep`. |
| `plans/` | Reserved for human-authored implementation plans; never auto-managed (the orchestrator creates the folder via STEP 0 but no step writes to it). |
| `summary/latest-run.md` | Latest run summary; overwritten every run. |
| `summary/runs/YYYYMMDD-HHMMSS.md` | Timestamped run history; never overwritten. |

For per-document content expectations, see the architecture and conventions docs themselves.

In addition to `OUTPUT_ROOT/`, the project-root `CLAUDE.md` is updated in STEP 0 (initial migration) and STEP 8 (final reconciliation). See [CLAUDE.md Integration](#claudemd-integration).

## Interactive Moments

The skill is mostly autonomous. Three points stop and ask the user.

### STEP 0 — Mixed Project Without Output Root

If `PROJECT_TYPE = mixed` is detected (both frontend and backend indicators present) AND `$ARGUMENTS` is empty, the orchestrator stops and asks the user to either re-run from a specific app subdirectory or pass an explicit output root (orchestrator § STEP 0 — Detect PROJECT_TYPE). When an output root is supplied, the run proceeds without prompting.

### STEP 0 — Missing Required Agent

Pre-flight verifies that all six agent files exist in `.claude/agents/` (orchestrator § STEP 0 — Verify required agents). If any are missing, the workflow hard-stops and reports:

1. which agent file is missing
2. which file path was expected
3. which step cannot continue
4. what the user needs to create or fix

The orchestrator never silently falls back to executing agent work in the supervisor context (orchestrator § Hard requirement).

### STEP 0.4 — Uncommitted Doc Edits

When the docs folder has uncommitted changes at the start of a run (and `mode != force`), the orchestrator lists the affected files and prompts:

> These files have uncommitted changes (possible manual edits): `[list]`. Agents will treat current file contents as canonical and apply incremental updates, but cannot guarantee manual edits in rewritten sections are preserved. Continue? [y/N]

(orchestrator § STEP 0.4 — Manual edit detection)

- **N** — exit. No files are touched.
- **Y** — proceed. Existing file contents are read as the baseline for incremental updates.

### STEP 0.4 — No Changes Detected

If no source or doc changes are found since the last docs commit, the orchestrator prompts: "no changes detected since last run — Force re-run? [y/N]" (orchestrator § STEP 0.4 — Step scoping via git diff). N exits, Y runs all steps.

### STEP 7 — Correction Confirmation

In full mode, after the audit (STEP 6) returns a prioritized correction list, the orchestrator presents the High and Medium findings to the user and waits for confirmation before touching any file (orchestrator § STEP 7). Low-priority findings are reported but never applied. The user can selectively confirm which High/Medium items to apply.

This is the only point in the workflow where docs files are modified based on user choice rather than autonomous logic.

## Idempotency and Re-Runs

The skill is designed for repeated execution. Three guarantees keep re-runs cheap and predictable.

### Stable File Paths

Filenames do not drift between runs. The same `architecture/overview.md`, `conventions/coding.md`, etc. are written each time, so links and CLAUDE.md references stay valid (orchestrator § When writing files).

### Incremental Updates Over Rewrites

Agents read existing file contents as the baseline and apply incremental updates rather than full rewrites where possible (orchestrator § When writing files and § STEP 7). Hand edits in unaffected sections survive a re-run; sections that are regenerated may not preserve manual edits, which is why STEP 0.4 warns the user before proceeding.

### Git-Diff Scoping

When git is available, STEP 0.4 uses `git log` and `git diff` against the last docs commit to determine the minimum set of steps that need to re-run (orchestrator § STEP 0.4 — Step scoping via git diff). Source-only changes run STEPS 1-5 + 8 (plus 6, 7, 0.5, 0.6 in full mode); docs-only changes collapse to STEP 8; no changes triggers a force-rerun prompt. The result is intersected with the mode's permitted step set.

When git is unavailable or the project is not a git repo, both idempotency checks are skipped and all steps run (orchestrator § STEP 0.4 — Degraded mode). The skill never silently produces stale output because of a missing tool.

The recommended workflow after each run is to commit the result so the next run has a clean baseline:

```bash
git add docs/ CLAUDE.md
git commit -m "docs: update knowledge base"
```

## Behavioral Guarantees

The orchestrator and agent contracts give the user the following guarantees.

### Read-Only Agents Cannot Write

The `spec-brainstormer` (STEP 1) and `spec-auditor` (STEP 6) agents are scoped to read-only tools — their YAML frontmatter omits `Write`. This is enforced by the Claude Code harness at the tool level, not just by prose in the prompt. The brainstormer returns a structured analysis; the auditor returns a prioritized correction list. Neither can modify a file even if instructed to.

### Legacy Migrations Never Overwrite

STEP 0.5 moves legacy doc paths (`OUTPUT_ROOT/decisions/`, `OUTPUT_ROOT/specs/01-architecture.md`, `OUTPUT_ROOT/specs/03-api.md`) into the new taxonomy only when the destination is empty (orchestrator § STEP 0.5). When both the legacy and new locations contain different files, the conflict is reported and both files are left in place — the orchestrator never auto-resolves a conflict by overwriting.

STEP 0.6 (legacy consolidation) follows the same rule for content: legacy files are never deleted; durable content is distilled into canonical docs while the legacy file remains for human review (orchestrator § STEP 0.6).

### ADR Numbering is Collision-Free

ADR numbering is centralized in `adr-writer` (STEP 5). Before invoking the agent, the orchestrator runs `git pull` (or equivalent) to ensure the local `architecture/decisions/` folder reflects the latest remote state (orchestrator § STEP 5). Parallel ADR creation is explicitly forbidden unless a single coordinator owns numbering (orchestrator § STEP 5). Two contributors running the workflow at the same time will not collide on `NNNN-*.md` filenames.

### CLAUDE.md is Migrated, Not Replaced

When `CLAUDE.md` already exists, the orchestrator updates matching sections in place rather than appending duplicates (orchestrator § STEP 0 — Check and migrate CLAUDE.md). Project-specific guidance, domain language, and non-documentation rules are preserved. Legacy doc references are rewritten to point at the new taxonomy. STEP 8 reconciles a final time after all docs are generated (orchestrator § STEP 8).

### Every Run Persists a Summary

A run summary is written to `summary/latest-run.md` (overwritten) and a timestamped copy at `summary/runs/YYYYMMDD-HHMMSS.md` (never overwritten) on every run (orchestrator § Final run summary). The summary records the mode used, detected `PROJECT_TYPE`, agents invoked, all files created/modified/moved/skipped, migration actions, conflicts, remaining assumptions, and recommended next steps (orchestrator § Final run summary).

### Missing Agents Halt the Run

The orchestrator never silently performs agent work in the supervisor context. If a required agent file is unavailable (STEP 0 verification, or any step's invocation), the workflow stops immediately and reports the missing path, the affected step, and what the user needs to fix (orchestrator § Hard requirement).

## Project Type Auto-Detection

At pre-flight, the orchestrator inspects repository markers to set `PROJECT_TYPE`, which subagents use to adapt their analysis. Detection priority (orchestrator § STEP 0 — Detect PROJECT_TYPE):

| Detected Type | Trigger |
|---|---|
| `frontend` | `package.json` has any of `react`, `next`, `@angular/core`, `@angular/cli`, `vue`, `nuxt`, `astro` in dependencies or devDependencies |
| `backend-dotnet` | Any `*.csproj`/`*.sln`, or `Program.cs`/`Startup.cs` exists |
| `backend-node` | `package.json` has any of `express`, `fastify`, `koa`, `nestjs`, `hapi` |
| `mixed` | Both frontend and backend indicators present |

The orchestrator reports the detected type and the specific files that drove the decision before continuing.

## CLAUDE.md Integration

`CLAUDE.md` in the target project is touched at two well-defined points.

### STEP 0 — Initial Migration or Init

If `CLAUDE.md` does not exist, the orchestrator runs `/init` and then improves the result. If it exists, the orchestrator migrates it to the new doc taxonomy: existing matching sections (`## Architecture`, `## Conventions`, `## Specs`, `## ADR Workflow`, `## Documentation`) are updated in place; missing sections are appended from a standard template; legacy path references are rewritten (orchestrator § STEP 0 — Check and migrate CLAUDE.md). All non-documentation guidance already in the file is preserved.

### STEP 8 — Final Reconciliation

After all docs are generated, STEP 8 reconciles `CLAUDE.md` one final time so its references reflect what was actually produced — including `architecture/`, `conventions/`, `specs/`, `architecture/decisions/`, and `reference/` when reference docs exist (orchestrator § STEP 8). Any remaining legacy references are rewritten; matching sections are updated in place rather than duplicated.

The net effect is that after every run, Claude Code in the target project reads the right doc files automatically because `CLAUDE.md` directs it to them.

## Deployment Model

The skill is not a standalone application. It is deployed into a target project by copying files (one-time setup):

```bash
mkdir -p .claude/commands .claude/agents
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
```

After this, the slash command `/generate-knowledge-base` is available in the target project. The required runtime is the Claude Code harness; git is optional (it enables idempotency scoping and history-preserving migration). See `architecture/overview.md` for the full deployment and runtime shape.

## Out of Scope

The skill explicitly does NOT do any of the following:

- **Generate or modify source code.** It only produces markdown under `OUTPUT_ROOT/` and edits `CLAUDE.md`.
- **Run, build, or test the project.** The skill never executes the target's build/test commands.
- **Commit or push to git.** It suggests a `git add`/`git commit` command at the end of a run, but the user runs it themselves (orchestrator § Final run summary).
- **Deploy anything.** No infrastructure, no servers, no CI configuration.
- **Auto-resolve legacy doc conflicts.** When the legacy and new locations both contain content, the conflict is reported, not merged.
- **Delete legacy files.** Legacy docs are preserved as historical context until a human removes them (orchestrator § STEP 0.6).
- **Apply Low-priority audit findings.** Only High and Medium items are eligible for application, and only after explicit user confirmation (orchestrator § STEP 6 and § STEP 7).
- **Manage `OUTPUT_ROOT/plans/`.** The plans folder is reserved for human-authored implementation plans and is never auto-managed (orchestrator § Documentation intent).
- **Run outside Claude Code.** There is no programmatic, HTTP, or CLI entry point separate from the slash command.

## Assumptions

- `$ARGUMENTS` parsing is by natural-language pattern match — the orchestrator looks for the literal `mode=` prefix to extract the mode and treats the remainder as `OUTPUT_ROOT`. There is no formal argument parser, so unusual inputs (e.g., a path containing `mode=` as a substring) may be misclassified.
- The `mixed` project-type guard checks whether `$ARGUMENTS` is non-empty, not whether it contains a valid output-root path. An invocation like `/generate-knowledge-base mode=light` against a mixed project will satisfy the guard even though no output root was supplied.
- The `YYYYMMDD-HHMMSS` timestamp in `summary/runs/` uses the local timezone of the machine running Claude Code; the orchestrator does not specify UTC.
- Light-mode skip conditions are individually overridable by an explicit user request (each of orchestrator § STEP 0.5, § STEP 0.6, § STEP 5, § STEP 6, and § STEP 7 says "unless the user explicitly requests").
- The Superpowers plugin integration described in the orchestrator's § Superpowers usage is genuinely optional and produces no externally visible behavior change. It is therefore out of scope for this spec.
- When `PROJECT_TYPE` matches none of the four documented detection rules (e.g., a documentation or tooling repo), behavior is determined ad hoc. The orchestrator does not enumerate fallback types in its detection rules.
- "Manual edits in rewritten sections are not preserved" is a stated limitation of the incremental-update model; the precise heuristic for what counts as a rewritten section is not specified by the orchestrator.
