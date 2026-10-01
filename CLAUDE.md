# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Personal workflow preferences (tone, engineering standards, commit and review habits) come from `~/.claude/CLAUDE.md`. Do not copy them into this file: a copy drifts, and an earlier copy broke the sections other files cite.

## Project Overview

This repository is a **collection of Claude Code skills**. Three skills currently live here:

| Skill | Command | Purpose |
|---|---|---|
| `generate-knowledge-base` | `/generate-knowledge-base` | Analyzes any software project and generates a structured knowledge base: architecture docs, conventions, specs, ADRs, and API references. |
| `generate-prd` | `/generate-prd` | Turns customer conversation transcripts into a PRD via a typed-critic discovery loop. Pure-conversation discovery — never reads the host codebase. |
| `development-workflow` | `/development-workflow` | Runs one piece of engineering work through the Ouroboros → Superpowers pipeline (classify, Seed, design/plan, execute, evaluate, finish) as a resumable state machine with human gates. |

None is a standalone application. The two `generate-*` skills are multi-agent orchestrators deployed _into_ target projects via `.claude/commands/` and `.claude/agents/` and invoked from within those projects. `development-workflow` is a single skill installed at user level (`~/.claude/skills/development-workflow/`) and invoked explicitly; it dispatches its own reviewer subagents and does not use the `Agents/` pattern.

## Commands

```bash
# generate-prd static tests (no API key)
pip install -r generate-prd/requirements-dev.txt
pytest generate-prd/tests/

# LLM-judge regression grader for generate-knowledge-base output (needs ANTHROPIC_API_KEY and `pip install anthropic pydantic`)
python scripts/smoke_grade.py --baseline ./kb-baseline/docs --new ./kb-new/docs

# Regenerate this repo's docs/ after changing a skill (run inside Claude Code)
/generate-knowledge-base mode=light

# Optional pre-push docs hook, installed per clone
bash scripts/install-hooks.sh

# development-workflow eval sandbox (flags: --with-resume | --empty | --at-phase4 | --at-phase2-design | --seed-mismatch | --legacy-seed)
bash development-workflow/evals/files/build-fixtures.sh <dest> [flag]
```

## Repository Structure

**`generate-knowledge-base/`**
- `generate-knowledge-base.md` — Orchestrator skill definition. Deploys to `.claude/commands/`. Defines a 12-step phase-based workflow (STEP 0 through STEP 8) that delegates analytical work to subagents.
- `Agents/` — Six subagent definitions (`[a-z]*-*.md`) deployed to `.claude/agents/`, plus a `README.md` that is not deployed.
- `docs/` — Install guide and walkthrough.
- `README.md` — User-facing overview.

**`generate-prd/`**
- `generate-prd.md` — Orchestrator skill definition. Deploys to `.claude/commands/`. Defines a 7-step workflow (STEP 0–6): normalize → distill → cluster → draft → discovery loop → finalize.
- `Agents/*.md` — Six subagent definitions deployed to `.claude/agents/`.
- `prompts/` — Seven prompt files read at runtime by the agents (not deployed).
- `schema/` — State schema (JSON Schema draft 2020-12), PRD template, transcript format spec, migration scaffolding.
- `tests/` — Static test suite (no API key required) + golden corpus + durability playbooks.
- `docs/` — Install guide and walkthrough. The user-facing README is `generate-prd/README.md`.

**`development-workflow/`**
- `README.md` — User-facing overview: pipeline diagram, gates, model split, requirements, install, eval sandbox.
- `SKILL.md` — The skill definition: Phases 0–5, state tracking, artifact storage. Source of truth.
- `references/*.md` — Detail loaded on demand from named phases (Phase 3 execution and worktree mechanics, Phase 4 QA call, reviewer brief and controller handling, Seed edge cases, Seed QA refinement, doc baseline and Phase 5 backstop, run lifecycle details, engineering defaults).
- `DESIGN.md` — Dated design decisions and audit history. Not installed.
- `evals/` — `evals.json` (test prompts with expectations) and fixtures. Not installed.

**Repo-level**
- `docs/` — The knowledge base generated for this repo by `generate-knowledge-base` (architecture, conventions, specs, reference, ADRs).
- `scripts/` — Dev tooling: `smoke_grade.py` (LLM-judge regression grader), `hooks/pre-push` and `install-hooks.sh` (see Gotchas for what the hook covers).

## Architecture

- Architecture docs live in docs/architecture/
- Read docs/architecture/overview.md before making structural or architectural changes
- Read docs/architecture/components.md and docs/architecture/integrations.md when working in unfamiliar areas

The workflow described here and in Orchestrator Flow below is `generate-knowledge-base`'s; `generate-prd` follows the same shape with its own STEP 0–6. The workflow is **supervisor-led and phase-based** — the orchestrator runs steps sequentially and delegates analytical/writing work to specialized subagents. No overlapping write operations run in parallel.

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

This section governs the agents of the two `generate-*` skills. `development-workflow` has its own policy, defined in its `SKILL.md` (`opusplan` routing plus an explicit `model:` on every subagent it dispatches). The rule to use generic aliases and never pin a version applies to all three.

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
| `prd-critic` (`generate-prd`) | `opus` | `high` | Typed findings gate every discovery-loop iteration. |
| `prd-drafter`, `transcript-normalizer` (`generate-prd`) | `sonnet` | `medium` | Structured transformation with a clear input and schema. |
| `transcript-distiller` (`generate-prd`) | `sonnet` | `medium` (`high` for a transcript over ~10k tokens) | Bounded extraction; length is the only escalation trigger. |
| `theme-clusterer`, `prd-finalizer` (`generate-prd`) | `sonnet` | `high` | Cross-transcript reasoning and a one-shot completeness audit; quality compounds. |

Mechanics:
- **Model**: the agent's frontmatter `model:` is the single source of truth. Use generic aliases (`opus` / `sonnet` / `haiku` / `inherit`). Never pin a specific version (e.g. `claude-opus-4-6`) — pins miss model improvements. **Exception**: dev tooling under `scripts/` and `generate-prd/tests/validators/` that calls the Anthropic SDK directly must use specific model IDs (e.g. `claude-opus-4-7`) because the SDK does not resolve aliases. This carve-out is scoped strictly to dev tooling — orchestrator and agent frontmatter must use generic aliases.
- **Effort**: set by the orchestrator via `/effort <level>` before each `Agent` dispatch. Default is `medium`; escalate to `high` around `spec-brainstormer`, `adr-writer`, `spec-auditor`, then revert. `generate-prd` sets its own per-step schedule in its orchestrator (`high` for `theme-clusterer`, `prd-critic` and `prd-finalizer`, and for `transcript-distiller` on long transcripts); the table above mirrors it.
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
cp /path/to/generate-knowledge-base/Agents/[a-z]*-*.md .claude/agents/   # skips Agents/README.md
# Then run: /generate-knowledge-base
```

`development-workflow` installs at user level instead:

```bash
mkdir -p ~/.claude/skills/development-workflow
cp -r development-workflow/SKILL.md development-workflow/references ~/.claude/skills/development-workflow/
```

## Gotchas

- Other files cite `§ Model and Effort Policy` and the ADR Workflow section by name. Don't rename those headings.
- `generate-knowledge-base` STEP 8 updates matching Architecture, Conventions, Specs, ADR Workflow and Documentation sections of this file in place, and appends any that are missing. Don't merge or rename them, or the next run may add duplicates. The hand-written Orchestrator Flow, Subagent Roles and Key Design Decisions live under `## Architecture`, so check them after each run.
- `docs/` is generated. Uncommitted manual edits trigger the STEP 0.4 "possible manual edits" prompt on the next run, so commit them first.
- ADRs are history. Supersede one with a new ADR; the only edit to an old one is its status line (ADR 0001 still shows the old deploy glob on purpose).
- `development-workflow/SKILL.md` uses CRLF line endings, unlike the other files. A Python text-mode rewrite flattens them and turns the diff into thousands of changed lines; edit it with a CRLF-preserving tool.
- `scripts/hooks/pre-push` isn't installed by default, and it watches only `generate-knowledge-base/` and `generate-prd/`, not `development-workflow/`.
- `development-workflow/evals/evals.json` holds authored prompts and expectations. Nothing runs them automatically.

## When Modifying This Project

### `generate-knowledge-base`
- The orchestrator (`generate-knowledge-base.md`) is the source of truth for step ordering, agent delegation rules, mode behavior, and safety policies. Agent files must stay consistent with what the orchestrator expects.
- Agent frontmatter (`name`, `description`, `tools`) must match how the orchestrator invokes them. If you rename an agent or change its tool set, update the orchestrator's verification list in STEP 0 and the corresponding invocation.
- ADR numbering is centralized in `adr-writer` with a deduplication procedure — this is intentional to prevent collisions. Do not add parallel ADR creation without a numbering coordinator.
- The safe parallelism policy in the orchestrator is load-bearing — relaxing it risks file corruption when multiple agents write overlapping targets.

### `generate-prd`
- The orchestrator (`generate-prd.md`) is the source of truth for the STEP 0–6 phase machine, checkpoint-before-API-call invariant, stuck-loop fault detection, and state schema version. Agent files must stay consistent with what the orchestrator expects.
- The state schema (`schema/state.schema.json`) is versioned. If you change the schema shape, bump `schema_version`, add a migration script at `schema/migrations/v<from>-to-v<to>.py`, and update the orchestrator's STEP 0 version check.
- The model and `/effort` schedule in the orchestrator is intentional (the table in Model and Effort Policy mirrors it) — do not flatten it without reviewing that policy.
- After any change to orchestrator or agent files, run `pytest generate-prd/tests/` to confirm the static suite still passes (install its dependencies first, see Commands).

### `development-workflow`
- `SKILL.md` is the source of truth for the phase order, gates and state tracking; `references/*.md` are loaded from named phases and must stay consistent with it.
- Keep the installed copy at `~/.claude/skills/development-workflow/` identical to the repo copy; it is a manual copy and drifts silently. In practice it also holds `DESIGN.md`; the install command above copies only `SKILL.md` and `references/`, which is enough to run the skill. `evals/` stays in the repo.
- A model-policy change touches `SKILL.md`, `references/phase3-execution.md`, `references/phase4-qa.md`, `references/reviewer-brief.md` (it sets `model: opus` on reviewers), the model assertions in `evals/evals.json`, the model lines in this file's Model and Effort Policy and in `~/.claude/CLAUDE.md` (Plan Mode), the root README's Requirements section and Phase 3 row, `development-workflow/README.md` (its pipeline diagram, Model split and Requirements), and a dated section in `DESIGN.md`.
- Phase 0 preflight changes and `evals/evals.json` move together with `SKILL.md`; both READMEs state the eval count (`development-workflow/README.md` in two places, the root README in its structure block), and a gate or state-field change also touches the fixtures in `evals/files/build-fixtures.sh`.

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
