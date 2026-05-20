# Architecture Overview

## Repository Scope

This repository contains two sibling Claude Code skills. This document covers `generate-knowledge-base`; the `generate-prd` skill has its own design spec at [`docs/specs/2026-05-15-generate-prd-design.md`](../specs/2026-05-15-generate-prd-design.md) and user docs under `generate-prd/docs/`. The two skills share design DNA (markdown-orchestrator + subagent pattern, MADR ADRs) but are never coupled — they run independently and do not read each other's outputs.

## System Purpose

`generate-knowledge-base` is a Claude Code custom slash-command skill (`/generate-knowledge-base`) plus six subagents that, when deployed into a target project's `.claude/` folder, produce an evidence-based knowledge base under that project's `docs/` tree.

It is not a runtime service or library. The repository contains no compiled artifacts, no application entry point, no HTTP API, and no datastore. Every component is a markdown file with YAML frontmatter that the Claude Code runtime interprets at invocation time. See the frontmatter of `generate-knowledge-base/generate-knowledge-base.md` for the skill declaration (`description`, `allowed-tools`, `model`).

Given any software repository, the workflow performs a deep codebase analysis and emits architecture docs, coding conventions, product specs, architectural decision records (ADRs), and (when applicable) an API reference. Output is designed to be re-run as the codebase evolves, applying incremental updates rather than full rewrites.

## Core Use Cases

1. **First-time onboarding** — generate a complete docs baseline (architecture, components, integrations, conventions, specs, optional API reference, ADRs).
2. **Incremental refresh** — re-run on a codebase whose source has changed; STEP 0.4 uses git-diff scoping to skip unchanged steps.
3. **Out-of-band recovery** — `mode=force` bypasses git-diff scoping when the docs folder has drifted from git (e.g. a previous run's output was never committed).
4. **Quick refresh** — `mode=light` skips legacy migration, legacy consolidation, ADRs, audit, and corrections.

The public surface is the slash command itself plus its arguments: `[output-root-folder] [mode=full|light|force]`. There is no programmatic or HTTP entry point.

## Architectural Style

The system is a **supervisor-led, phase-based orchestration**:

- A single orchestrator file (`generate-knowledge-base.md`) controls all execution flow.
- Six specialized subagents under `Agents/` perform analytical and writing work.
- Steps execute strictly sequentially. Per the orchestrator's § Safe parallelism policy, "Do not run overlapping write operations in parallel."
- The orchestrator delegates to subagents via the Claude Code `Agent` tool, passing context (brainstorm reports, project type, output root) inline in the dispatch prompt rather than via file artifacts.

This is a **prompt-engineering architecture**, not a compiled software system. Agent boundaries are enforced by the `tools:` field in each agent's YAML frontmatter — read-only agents simply omit `Write`, and only the orchestrator declares the `Agent` tool, so only the supervisor can dispatch subagents.

## Execution Flow

The orchestrator defines a 12-step pipeline (STEP 0 through STEP 8, including intermediate steps 0.4, 0.5, and 0.6):

```
STEP 0    Pre-flight (always)
            - Detect PROJECT_TYPE from repo markers
            - Verify all 6 agent files exist in .claude/agents/
            - Initialize or migrate CLAUDE.md (runs /init when missing)
            - Create output folder structure with .gitkeep where empty

STEP 0.4  Idempotency pre-flight (skipped in mode=force)
            - Git-diff scoping: determine which steps need re-execution
              based on what changed since the last docs commit
            - Manual edit detection: warn about uncommitted doc changes

STEP 0.5  Legacy doc migration (mode=full only)
            - Safe filesystem moves via `git mv` (orchestrator-direct)

STEP 0.6  Legacy doc consolidation (mode=full only)
            - Editorial merge of legacy content into canonical docs
            - Delegated to legacy-doc-consolidator agent

STEP 1    Brainstorm (always; read-only)
            - Deep codebase analysis via spec-brainstormer agent
            - Returns a structured report consumed by later steps

STEP 2    Architecture docs (always)
            - spec-writer agent generates overview, components, integrations
            - Generates reference/api.md ONLY when the codebase has an
              API surface (HTTP routes, GraphQL schemas, gRPC services,
              public library exports, or consumed-API clients). No stub
              file is created when no API surface is detected.

STEP 3    Conventions docs (always)
            - conventions-writer agent generates coding/testing/naming/api

STEP 4    Specs (always)
            - spec-writer agent (second invocation) generates specs/00-overview.md
              (and additional feature specs only when clearly supported)

STEP 5    ADRs (mode=full only)
            - adr-writer agent identifies 3-5 significant decisions and
              writes MADR-format files; runs `git pull` first to keep
              numbering authoritative across concurrent contributors

STEP 6    Audit (mode=full only; read-only)
            - spec-auditor agent returns a prioritized correction list

STEP 7    Apply corrections (mode=full only)
            - Orchestrator confirms High/Medium corrections with the user
              and applies only the confirmed subset

STEP 8    Finalize CLAUDE.md (always)
            - Reconcile any remaining legacy references in CLAUDE.md
```

The hard requirement (orchestrator § Hard requirement) is that STEPS 1, 2, 3, 4, 5, 6, and 0.6 must delegate to their named subagent. If a required agent file is missing, the orchestrator stops immediately and reports which step cannot continue.

## Execution Modes

Three modes control which steps run; the per-step skip condition is intersected with the mode's permitted step set (the more restrictive wins).

| Mode | Behavior |
|---|---|
| `full` (default) | Runs the complete workflow including legacy migration, consolidation, ADRs, audit, corrections, and CLAUDE.md finalization. |
| `light` | Skips STEP 0.5, STEP 0.6, STEP 5, STEP 6, and STEP 7. Always runs STEPS 0, 0.4, 1, 2, 3, 4, and 8. |
| `force` | Identical to `full` but bypasses the STEP 0.4 git-diff scoping and uncommitted-change confirmation. Used when the docs folder is out of sync with git. |

## Idempotency Model

STEP 0.4 keeps re-runs cheap and safe:

- **Step scoping** — `git log -1 --format="%H" -- "$OUTPUT_ROOT"/` finds the last docs commit; `git diff $LAST_SHA HEAD --name-only` determines which paths changed. Source-only changes run STEPS 1–5 + 8 (plus STEPS 0.5, 0.6, 6, and 7 in full mode); docs-only changes collapse to STEP 8; no changes triggers a "force re-run?" prompt.
- **Manual edit detection** — `git diff HEAD -- "$OUTPUT_ROOT"/` lists uncommitted edits in the docs folder and prompts the user before agents touch those files.
- **Degraded mode** — if `git` is unavailable or the project is not a git repo, both checks are skipped and all steps run.

## Safe Parallelism Policy

The orchestrator is supervisor-led and phase-based. Parallel fan-out is allowed only inside a step when all of the following hold (orchestrator § Safe parallelism policy):

- each parallel task works on independent inputs
- each parallel task writes to a distinct target file or returns read-only analysis
- the step defines an explicit fan-in summary before downstream work continues

Explicitly disallowed: writes to the same markdown file, CLAUDE.md migration or finalization, ADR numbering and creation unless numbering is centralized, and correction application across overlapping target files.

When fan-out is used, the agent producing the step must emit a fan-in summary that lists each subtask, records success/failure/skipped status, merges non-conflicting findings, and surfaces conflicts explicitly rather than silently resolving them.

## Model and Effort Policy (token hygiene)

The skill operates on two declarative axes — model (Sonnet / Opus / Haiku) and reasoning effort (low / medium / high / max). Sources of truth:

- **Per-agent model** is declared in each agent's frontmatter `model:` field. Generic aliases only — never a pinned version.
- **Per-step effort** is set by the orchestrator via `/effort <level>` immediately before the relevant `Agent` dispatch. Default is `medium`; the orchestrator escalates to `high` before STEP 1 (`spec-brainstormer`), STEP 5 (`adr-writer`), and STEP 6 (`spec-auditor`), then reverts to `medium` after each.
- If `/effort` is unavailable in the harness, the orchestrator continues and behaves as if the requested level were applied.

See `components.md` for the full per-agent model table; the policy itself is defined in the orchestrator's § Model and effort policy and `CLAUDE.md` § Model and Effort Policy.

## Deployment and Runtime Shape

The skill ships as files in this repository's `generate-knowledge-base/` directory. Installation into a target project is a pure filesystem copy:

```bash
mkdir -p .claude/commands .claude/agents
cp generate-knowledge-base/generate-knowledge-base.md .claude/commands/
cp generate-knowledge-base/Agents/*.md .claude/agents/
```

At runtime, Claude Code in the target project loads the orchestrator as a custom slash command and resolves subagents from `.claude/agents/`. There is no service to start, no port to bind, no process to manage. The orchestrator's only persistent side effects are the markdown files it writes under `OUTPUT_ROOT/` and the project-root `CLAUDE.md`.

This repository self-hosts: its own `docs/` tree is the prior run's output and is regenerated by running the skill on itself.

## Output Taxonomy

```
docs/
  architecture/{overview,components,integrations}.md
  architecture/decisions/NNNN-*.md           (MADR-format ADRs)
  conventions/{coding,testing,naming,api}.md
  specs/00-overview.md                       (+ optional feature specs)
  reference/api.md                           (only when project has APIs)
  plans/                                     (preserved, never auto-managed)
  summary/latest-run.md
  summary/runs/YYYYMMDD-HHMMSS.md
```

Folder intent (orchestrator § Documentation intent):

- `architecture/` — long-lived system knowledge.
- `architecture/decisions/` — MADR-format ADRs.
- `conventions/` — stable implementation rules and team conventions.
- `specs/` — product and feature specifications.
- `plans/` — implementation plans and execution checklists; never auto-managed.
- `reference/` — durable lookup documentation (APIs, configuration, schemas).
- `summary/` — persistent summaries of orchestration runs, plus a timestamped history under `summary/runs/`.

For this repository specifically, `reference/api.md` is not generated and the file does not exist: the skill exposes no HTTP, RPC, or programmatic API — only the slash-command interface. The `docs/reference/` folder is tracked by its `.gitkeep`; the absence of `api.md` is the correct shape per the API-presence rule in `spec-writer.md` § API-presence rule.

## Important Constraints

- **Markdown-only.** No source-code language indicators apply. The skill cannot be packaged as an installable library.
- **Claude Code harness is mandatory.** The skill cannot run outside the Claude Code runtime; it depends on the `Agent`, `Read`, `Write`, `Bash`, `Glob`, and `Grep` tools and on slash-command dispatch.
- **Subagents are stateless.** Each agent invocation receives all needed context inline; there is no shared memory other than files on disk.
- **No silent fallbacks for missing agents.** If any required agent file is absent, the orchestrator halts and reports the missing path — it does not fall back to in-context execution.
- **ADR numbering is centralized.** Numbering and deduplication are owned by `adr-writer` to prevent collisions; parallel ADR creation is explicitly forbidden unless a single coordinator owns numbering (orchestrator § STEP 5).

## Assumptions

- The Claude Code harness resolves the generic model aliases (`opus`, `sonnet`, `haiku`, `inherit`) to the latest matching model at dispatch time. The skill never observes the resolved version.
- "Target project" is a separate repository from this source repository; the Quick Start does not explicitly forbid running the skill against itself, but the dogfooded `docs/` tree implies the workflow is self-hostable.
- The Superpowers plugin is genuinely optional — no canary explicitly verifies its absence; the orchestrator simply checks for `.claude/skills/superpowers` or `.claude/settings.json` and proceeds either way.
- The repository's local `.claude/` directory is dev-time configuration for this project and is not part of the deployable skill surface.
