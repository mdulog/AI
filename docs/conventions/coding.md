# Coding Conventions

This project is a pure-markdown Claude Code skill. There is no compiled code, no build system, no test runner, and no runtime dependencies beyond the Claude Code harness. "Code" here means YAML frontmatter and structured markdown prompts that the runtime interprets at invocation time.

These conventions distinguish **required patterns** (declared or enforced by the orchestrator/agent files themselves) from **observed conventions** (recurring across files but not formally enforced).

## YAML Frontmatter

### Required: Orchestrator (Command File) Frontmatter

The orchestrator command file (`generate-knowledge-base/generate-knowledge-base.md`) declares exactly these top-of-file keys:

| Key | Required | Purpose |
|---|---|---|
| `description` | Yes | One-line summary shown in Claude Code's command list |
| `allowed-tools` | Yes | Array of Claude Code tools the command may use |
| `model` | Yes | Generic model alias for the orchestrator thread |
| `# accepted-arguments` | No | A commented-out documentation hint of the argument schema; not an active frontmatter field |

Verbatim shape (frontmatter of `generate-knowledge-base/generate-knowledge-base.md`):

```yaml
---
description: Generates and maintains a project knowledge base for an existing software project
allowed-tools: [Read, Write, Bash, Agent]
# accepted-arguments: [output-root-folder] [mode=full|light|force]
model: sonnet
---
```

The `# accepted-arguments` line is a comment — it is for human readers and is not parsed by the runtime.

### Required: Agent (Subagent) Frontmatter

Every agent file under `generate-knowledge-base/Agents/` declares exactly these four keys, in this order:

| Key | Required | Purpose |
|---|---|---|
| `name` | Yes | Identifier the orchestrator uses to invoke the agent; must equal the filename without extension |
| `description` | Yes | One-line summary shown in agent listings and used by the orchestrator for identification |
| `tools` | Yes | Array of Claude Code tools the agent is permitted to use |
| `model` | Yes | Generic model alias for that agent's thread (single source of truth — see Model and Effort Policy) |

Verbatim shape (frontmatter of `generate-knowledge-base/Agents/spec-brainstormer.md`):

```yaml
---
name: spec-brainstormer
description: Analyzes the repo and CLAUDE.md to understand purpose, layers, patterns, services, and integration points.
tools: [Read, Bash, Glob, Grep]
model: opus
---
```

All six agent files use this identical four-field shape (verified against `spec-brainstormer.md`, `spec-writer.md`, `conventions-writer.md`, `legacy-doc-consolidator.md`, `adr-writer.md`, `spec-auditor.md`).

### Required: Key-Name Difference Between Commands and Agents

Commands use `allowed-tools`; agents use `tools`. The two keys serve the same purpose (declaring permitted Claude Code tools) but are not interchangeable — this is a Claude Code platform convention. Both accept a YAML inline array using the same tool names.

## Model and Effort Policy

The skill operates on two declarative axes — **model** (Sonnet / Opus / Haiku) and **reasoning effort** (low / medium / high / max). The full policy lives in `CLAUDE.md` § Model and Effort Policy and the orchestrator's § Model and effort policy; the rules below are quoted/restated verbatim where applicable.

### Required: Model Rule

1. **Sonnet** is the default.
2. **Opus** is used only where escalation is justified by complexity, ambiguity, or compounding output quality.
3. **Haiku** is reserved for narrow mechanical chores — no current subagent qualifies.

### Required: Effort Ladder

1. **Sonnet + medium** — default for orchestration and standard generation.
2. **Sonnet + high** — try this before escalating model.
3. **Opus + high** — truly hard tasks (current Opus agents sit here).
4. **Opus + max** — rare, highest-stakes reasoning; no current step qualifies.
5. **Haiku + low** — narrow mechanical chores; no current step qualifies.

### Required: Sources of Truth

- **Per-agent model**: declared once in the agent's frontmatter `model:` field. This is the single source of truth. The orchestrator never overrides `model` on an `Agent` invocation (orchestrator § Model and effort policy: "Do not add per-step `model` overrides on `Agent` invocations").
- **Per-step effort**: set by the orchestrator via `/effort <level>` immediately before each `Agent` dispatch.

### Required: Generic Aliases Only — No Version Pins

Use generic aliases (`opus`, `sonnet`, `haiku`, `inherit`). **Never pin a specific version** (e.g. `claude-opus-4-6`, `claude-opus-4-7`). Pinned versions miss model improvements over time. This rule is stated in `CLAUDE.md` § Model and Effort Policy and the orchestrator's § Model and effort policy.

**Dev-tooling carve-out:** `scripts/smoke_grade.py` hardcodes `JUDGE_MODEL = "claude-opus-4-7"` (see the `JUDGE_MODEL` constant near the top of the script). The Anthropic Python SDK does not resolve generic aliases — it requires an exact model ID — so dev tooling that calls the SDK directly is exempt from the no-pins rule. This carve-out is codified in `CLAUDE.md` § Model and Effort Policy. Bump the pin on model launches; do NOT propagate the pinned-version pattern into orchestrator or agent frontmatter, which the harness DOES alias-resolve.

### Required: Effort Schedule

The orchestrator issues these `/effort` directives (§ Model and effort policy):

- `/effort medium` at session start; remains `medium` for STEPS 0, 0.4, 0.5, 0.6, 2, 3, 4, 7, 8.
- `/effort high` immediately before invoking `spec-brainstormer` (STEP 1), `adr-writer` (STEP 5), and `spec-auditor` (STEP 6); reverted to `medium` after each dispatch.
- If `/effort` is unavailable in the harness, the orchestrator continues and behaves as if the requested level were applied.

A new subagent added without a `model:` field inherits `sonnet` from the orchestrator — a safe default per `CLAUDE.md` § Model and Effort Policy.

## Tool-Set Boundaries

### Required: Tool Sets Enforce Write Boundaries

Agent boundaries are enforced at the tool-permission level, not in prose:

| Component | Tool set | Can write files? | Can dispatch agents? |
|---|---|---|---|
| Orchestrator | `[Read, Write, Bash, Agent]` | Yes | Yes |
| `spec-brainstormer` | `[Read, Bash, Glob, Grep]` | **No** | No |
| `spec-writer` | `[Read, Write, Bash, Grep]` | Yes | No |
| `conventions-writer` | `[Read, Write, Bash, Glob, Grep]` | Yes | No |
| `legacy-doc-consolidator` | `[Read, Write, Bash, Glob, Grep]` | Yes | No |
| `adr-writer` | `[Read, Write, Bash, Glob]` | Yes | No |
| `spec-auditor` | `[Read, Bash, Glob, Grep]` | **No** | No |

Two consequences are load-bearing:

- **Read-only agents lack `Write`.** `spec-brainstormer` and `spec-auditor` cannot modify any file — the harness denies the call. Prose rules (e.g. "Never create or modify any files") reinforce but do not implement the boundary.
- **Only the orchestrator declares `Agent`.** Subagents cannot dispatch other subagents; only the supervisor can.

### Observed: Write-Path Scoping by Prose

`Write` itself accepts any path. Restricting writes to specific subtrees (e.g. "spec-writer only writes under `OUTPUT_ROOT/architecture/` and `OUTPUT_ROOT/reference/`") is enforced by the orchestrator's dispatch prompt and the agent's own instructions — not by a path-level harness primitive. Adhere to the prose scoping in every agent file when adding new write targets.

## Markdown Prompt Structure

### Required: Common Prompt Skeleton

Every agent file follows the same top-level skeleton (verified across all six agents):

1. **Role declaration** — single opening sentence: "You are the [role] agent for this project."
2. **Inputs section** — bullet list of what the agent receives (`CLAUDE.md`, codebase, orchestrator variables, prior reports).
3. **Variable binding paragraph** — states that `PROJECT_TYPE` and `OUTPUT_ROOT` are passed by the orchestrator and must be treated as ground truth.
4. **Job description** — `Your job:` followed by a bullet list of responsibilities.
5. **Rules** — constraints, safety boundaries, and behavioral requirements.
6. **Output format / report requirements** — what the agent must return or produce.
7. **`## Assumptions`** — final section in the agent file (where applicable).

### Required: Variable-Binding Phrasing

Every agent prompt contains this exact instruction (verbatim):

> Variables (`PROJECT_TYPE` and `OUTPUT_ROOT`) are passed by the orchestrator in the invocation prompt. Treat them as ground truth; do not attempt to re-derive them.

Two agents are exceptions: `legacy-doc-consolidator` and `spec-auditor` both receive only `OUTPUT_ROOT` (not `PROJECT_TYPE`). Their work is taxonomy- and audit-focused rather than project-type-sensitive — verified against the variable-binding paragraph in each of `Agents/legacy-doc-consolidator.md` and `Agents/spec-auditor.md`.

### Required: Generated Documents End with `## Assumptions`

Every generated documentation file (architecture, conventions, specs, ADRs, reference) must end with an `## Assumptions` section listing inferences and unverifiable claims. This requirement appears in the orchestrator (STEPS 2, 3, 4) and in each writing agent's prompt.

The same `## Assumptions` requirement applies to **agent output reports** (including read-only agents): the brainstorm report and the audit list both end with `## Assumptions`.

Format:

```markdown
## Assumptions
- Bullet list of anything inferred or not directly verifiable
```

## Safety Rules (load-bearing)

### Required: Evidence-Based Claims Only

All agents must support output with codebase evidence. The rule appears in equivalent form in every agent prompt:

- `spec-brainstormer`: "Only include claims supported by repository evidence."
- `spec-writer`: "Use Bash or Grep to verify codebase facts before writing — do not write claims you cannot confirm."
- `conventions-writer`: "Only include claims supported by code or existing docs."
- `adr-writer`: "Never invent decisions not supported by the code or existing docs."

### Required: Agent Delegation Enforcement

The orchestrator must delegate STEPS 1, 2, 3, 4, 5, 6, and 0.6 to their named subagents (orchestrator § Hard requirement). It must not perform that work in the main context. If a required agent file is missing, the orchestrator must hard-stop and report:

1. Which subagent is missing.
2. Which file path was expected.
3. Which step cannot continue.
4. What the user needs to create or fix.

There is no silent fallback to in-context execution.

### Required: No Overlapping Parallel Writes

The safe parallelism policy (orchestrator § Safe parallelism policy) prohibits parallel writes to the same file. Fan-out within a step is allowed only when **all** of:

- Each parallel task works on independent inputs.
- Each parallel task writes to a distinct target file or returns read-only analysis.
- The step defines an explicit fan-in summary before downstream work continues.

Explicitly forbidden from parallelization:

- Writes to the same markdown file.
- `CLAUDE.md` migration or finalization.
- ADR numbering and creation (unless a single coordinator owns numbering).
- Correction application across overlapping target files.

### Required: Mandatory Fan-In Summary

When fan-out is used, the agent producing the step must emit a fan-in summary that:

1. Lists each subtask.
2. Records success / failure / skipped status per subtask.
3. Merges non-conflicting findings.
4. Surfaces conflicts explicitly rather than silently resolving them.

This requirement appears in equivalent form in the orchestrator, `spec-brainstormer`, `legacy-doc-consolidator`, and `spec-auditor` prompts.

### Required: Never Delete Legacy Content

`legacy-doc-consolidator` and the orchestrator's STEP 0.5 / 0.6 instructions both forbid automatic deletion of legacy files. Legacy docs remain on disk as historical context until a human removes them. The consolidator's prompt states: "Preserve legacy docs; do not delete them."

### Required: ADR Numbering is Centralized

ADR numbering is owned exclusively by `adr-writer`. The agent (a) lists existing ADRs and their normalized topics, (b) decides per-candidate whether the topic is already covered (and updates the existing ADR if so, without assigning a new number), and (c) only after every candidate has been evaluated does it assign sequential `NNNN` numbers. The orchestrator runs `git pull` immediately before dispatching `adr-writer` (orchestrator § STEP 5) so the local `decisions/` folder reflects the latest remote state. Parallel ADR creation is forbidden unless a single coordinator owns numbering (orchestrator § STEP 5).

## Orchestrator-Specific Conventions

### Required: Strict Step Ordering

Steps execute strictly sequentially:

```
STEP 0 -> STEP 0.4 -> STEP 0.5 -> STEP 0.6 -> STEP 1 -> STEP 2 -> STEP 3 -> STEP 4 -> STEP 5 -> STEP 6 -> STEP 7 -> STEP 8
```

Steps may be skipped per execution mode or git-diff scoping, but the relative order never changes.

### Required: Execution Mode Semantics

| Mode | Steps included |
|---|---|
| `full` (default) | All steps |
| `light` | STEP 0, 0.4, 1, 2, 3, 4, 8 (skips 0.5, 0.6, 5, 6, 7) |
| `force` | All steps; bypasses STEP 0.4 git-diff scoping and uncommitted-change confirmation |

### Required: Incremental Updates Over Full Rewrites

Multiple files state this preference verbatim or near-verbatim:

- Orchestrator: "Prefer incremental updates over full rewrites." / "Keep filenames stable between runs."
- `spec-writer`: "Prefer incremental edits over complete rewrites when files already exist."
- `conventions-writer`: "Prefer updating existing docs in place rather than rewriting them from scratch."
- `legacy-doc-consolidator`: "Do not overwrite canonical docs wholesale when incremental updates are sufficient."

### Required: UTF-8 Markdown Output

The orchestrator (§ When writing files) requires UTF-8-encoded markdown for all generated files.

## GFM Formatting Requirements

### Required: Generated-Doc Structure

All generated documentation files use:

- GitHub-Flavored Markdown (GFM).
- UTF-8 encoding.
- H1 (`#`) for the document title.
- H2 (`##`) for major sections.
- H3 (`###`) for subsections.
- Final section: `## Assumptions`.

### Observed: Tables for Structured Information

Tables are used extensively across the orchestrator and agent prompts (tool permissions, step mappings, mode comparisons, frontmatter shapes). Generated docs follow the same pattern.

### Observed: Required vs Observed Labeling

Generated convention docs in this project use explicit `### Required:` and `### Observed:` H3 prefixes to distinguish enforced rules from recurring patterns. New convention sections should follow this labeling.

### Required: Cross-File Citations Use Section Anchors, Not Line Numbers

When citing another file from a long-lived doc (anything under `docs/architecture/`, `docs/conventions/`, `docs/specs/`, `docs/reference/`, or `docs/architecture/decisions/`), use a section-name anchor rather than a line number.

✅ Acceptable:

- `orchestrator § STEP 5`
- `CLAUDE.md § Model and Effort Policy`
- `Agents/spec-auditor.md (variable-binding paragraph)`
- the `JUDGE_MODEL` constant near the top of `scripts/smoke_grade.py`

❌ Forbidden:

- `orchestrator line 464`
- `CLAUDE.md lines 60–91`
- `Agents/spec-auditor.md line 19`
- `scripts/smoke_grade.py line 38`

**Why:** line numbers drift on every insertion or deletion in the cited file, silently invalidating the reference. Section names change only by deliberate rename, which is exactly when the citing reference *should* break loudly so a writer notices.

**When no section header exists** (e.g., an agent file with only frontmatter and a final `## Assumptions`, or a short script), use a descriptive anchor in parentheses such as `(frontmatter)`, `(variable-binding paragraph)`, or `(<symbol-name> constant)` rather than falling back to a line number.

**Exception:** code citations inside source files under `scripts/` or other implementation directories may reference line numbers when needed for review context — those references are usually short-lived. The rule above applies specifically to long-lived docs under `docs/`.

## Assumptions

- The `# accepted-arguments` comment in the orchestrator is parsed as a YAML comment by the runtime — not as a structured field. Its functional effect when uncommented is unverified.
- The `model:` resolution mechanism (generic alias → concrete model version) is performed by the Claude Code harness; the skill never observes the resolved version. Version drift is therefore invisible to the workflow by design.
- Prose-level write-path scoping (e.g. "spec-writer writes only under `OUTPUT_ROOT/architecture/`") relies on agent compliance with its instructions. There is no path-level enforcement primitive in the harness as of this run; if Claude Code adds one, the agent files should adopt it.
- The `scripts/smoke_grade.py` model pin is treated as a known dev-tooling exception. Whether the policy formally carves this out or the script should switch to the `opus` alias is unresolved.
- Line numbers cited in this document reflect the orchestrator at generation time; they will drift as the file evolves.
