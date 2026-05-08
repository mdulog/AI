# Coding Conventions

This project is a pure-markdown Claude Code skill. There is no compiled code, no build system, and no runtime dependencies beyond the Claude Code environment. "Code" in this context means YAML frontmatter and structured markdown prompts that define orchestrator and agent behavior.

## YAML Frontmatter

### Required: Command Files (Orchestrator)

Command files (deployed to `.claude/commands/`) use these frontmatter keys:

| Key | Required | Purpose |
|---|---|---|
| `description` | Yes | One-line summary shown in the Claude Code command list |
| `allowed-tools` | Yes | Array of Claude Code tools this command may use |
| `model` | Yes | Model identifier for the orchestrator thread |

The `accepted-arguments` key appears commented out in the orchestrator (line 4: `# accepted-arguments: [output-root-folder] [mode=full|light|force]`). This likely serves as inline documentation of the accepted argument schema rather than an active frontmatter declaration. Its functional effect when uncommented is unverified.

**Example** (from `generate-knowledge-base.md`):
```yaml
---
description: Generates and maintains a project knowledge base for an existing software project
allowed-tools: [Read, Write, Bash, Agent]
model: claude-opus-4-6
---
```

### Required: Agent Files (Subagents)

Agent files (deployed to `.claude/agents/`) use these frontmatter keys:

| Key | Required | Purpose |
|---|---|---|
| `name` | Yes | Identifier used by the orchestrator to invoke the agent |
| `description` | Yes | One-line summary shown in agent listings and used by the orchestrator for identification |
| `tools` | Yes | Array of Claude Code tools this agent is permitted to use |

Agents do not declare a `model` key. Model selection is inherited from the orchestrator or follows Claude Code defaults.

**Example** (from `spec-brainstormer.md`):
```yaml
---
name: spec-brainstormer
description: Analyzes the repo and CLAUDE.md to understand purpose, layers, patterns, services, and integration points.
tools: [Read, Bash, Glob, Grep]
---
```

### Observed: Key Name Difference Between Commands and Agents

Commands use `allowed-tools` while agents use `tools` for the same purpose (declaring permitted Claude Code tools). This appears to be a Claude Code platform convention rather than a project choice. Both use YAML array syntax with the same tool names.

## Markdown Prompt Structure

### Required: Prompt Sections

Every agent prompt follows a consistent top-level structure. The exact section names vary, but these categories are always present in the same order:

1. **Role declaration** -- A single opening sentence: "You are the [role] for this project."
2. **Inputs section** -- A bullet list of what the agent receives (CLAUDE.md, codebase, orchestrator variables, prior reports).
3. **Variable binding** -- A paragraph stating that `PROJECT_TYPE` and `OUTPUT_ROOT` are passed by the orchestrator and must be treated as ground truth.
4. **Job description** -- "Your job:" followed by a bullet list of responsibilities.
5. **Rules** -- Constraints, safety boundaries, and behavioral requirements.
6. **Output format** -- What the agent must return or produce, including file paths and structural requirements.

**Example pattern** (common across all 6 agents):
```markdown
You are the [role] agent for this project.

Inputs:
- `CLAUDE.md`
- The project codebase
- PROJECT_TYPE and OUTPUT_ROOT from the orchestrator

Variables (`PROJECT_TYPE` and `OUTPUT_ROOT`) are passed by the orchestrator in the invocation prompt.
Treat them as ground truth; do not attempt to re-derive them.

Your job:
- [responsibility 1]
- [responsibility 2]

Rules:
- [constraint 1]
- [constraint 2]

[Output format or report requirements]
```

### Required: Assumptions Section

Every generated documentation file and every agent output must end with an `## Assumptions` section. This applies at two distinct levels:

- **Generated documentation files**: required by the orchestrator in STEP 2, STEP 3, and STEP 4 instructions, and stated in each writing agent's prompt.
- **Agent output reports** (including read-only agents): the spec-brainstormer prompt ends with `## Assumptions`, and the report it returns follows this structure regardless of file-writing capability.

Format:
```markdown
## Assumptions
- Bullet list of anything inferred or not directly verifiable
```

### Required: Variable Passing Convention

The orchestrator passes `PROJECT_TYPE` and `OUTPUT_ROOT` to subagents as inline text in the Agent invocation prompt. Agents must treat these as ground truth and not attempt to re-derive them from the codebase. Every agent prompt contains this exact instruction:

> Variables (`PROJECT_TYPE` and `OUTPUT_ROOT`) are passed by the orchestrator in the invocation prompt. Treat them as ground truth; do not attempt to re-derive them.

The `legacy-doc-consolidator` is the one exception: it only receives `OUTPUT_ROOT` (not `PROJECT_TYPE`), because its work is taxonomy-focused rather than project-type-sensitive.

## Safety Rules

### Required: Read-Only Agents Must Not Write

Two agents are designated read-only and enforce this through tool permissions:

| Agent | Tools | Write Permitted |
|---|---|---|
| `spec-brainstormer` | Read, Bash, Glob, Grep | No |
| `spec-auditor` | Read, Bash, Glob, Grep | No |

The brainstormer prompt additionally states: "Never create or modify any files." The auditor prompt states: "Do NOT modify any files." These textual rules reinforce the tool-level enforcement.

### Required: No Overlapping Parallel Writes

The orchestrator's safe parallelism policy prohibits parallel writes to the same file. Fan-out within a step is allowed only when:

- Each parallel task works on independent inputs.
- Each parallel task writes to a distinct target file or returns read-only analysis.
- The step defines an explicit fan-in summary before downstream work continues.

Explicitly prohibited from parallelization:
- Writes to the same markdown file
- CLAUDE.md migration or finalization
- ADR numbering and creation (unless a single coordinator owns numbering)
- Correction application across overlapping target files

### Required: Fan-In Summary Structure

When fan-out parallelism is used within a step, the merged result must be a fan-in summary that:

1. Lists each subtask.
2. Records success, failure, or skipped status per subtask.
3. Merges non-conflicting findings.
4. Surfaces conflicts explicitly rather than silently resolving them.

This requirement appears in equivalent form (adapted to context) in the orchestrator, spec-brainstormer, legacy-doc-consolidator, and spec-auditor prompts.

### Required: No File Deletion of Legacy Content

The legacy-doc-consolidator and the orchestrator's STEP 0.5 both enforce that legacy files are never deleted. Legacy docs remain as historical context until a human removes them. The consolidator's prompt states:

> Preserve legacy docs; do not delete them.

### Required: Evidence-Based Claims Only

All agents must support their output with codebase evidence. This rule appears in every agent prompt in slightly different forms:

- Brainstormer: "Only include claims supported by repository evidence."
- Spec-writer: "Use Bash or Grep to verify codebase facts before writing -- do not write claims you cannot confirm."
- Conventions-writer: "Only include claims supported by code or existing docs."
- ADR-writer: "Never invent decisions not supported by the code or existing docs."

### Required: Agent Delegation Enforcement

The orchestrator must delegate STEPS 1, 2, 3, 4, 5, and 6 to named subagents. It must not perform that work in the main orchestration context. If a required agent is unavailable, the orchestrator must hard-stop and report:

1. Which subagent is missing.
2. Which file path was expected.
3. Which step cannot continue.
4. What the user needs to create or fix.

## Orchestrator-Specific Conventions

### Required: Step Ordering

Steps execute strictly sequentially. The orchestrator enforces this order:

```
STEP 0 -> STEP 0.4 -> STEP 0.5 -> STEP 0.6 -> STEP 1 -> STEP 2 -> STEP 3 -> STEP 4 -> STEP 5 -> STEP 6 -> STEP 7 -> STEP 8
```

Steps may be skipped based on execution mode or git-diff scoping, but the relative order never changes.

### Required: Execution Mode Semantics

| Mode | Steps Included |
|---|---|
| `full` (default) | All steps |
| `light` | STEP 0, 0.4, 1, 2, 3, 4, 8 |
| `force` | All steps, bypasses STEP 0.4 git-diff scoping |

### Required: Incremental Updates Over Full Rewrites

Multiple prompts state a preference for incremental updates:

- Orchestrator: "Prefer incremental updates over full rewrites."
- Orchestrator: "Keep filenames stable between runs."
- Spec-writer: "Prefer incremental edits over complete rewrites when files already exist."
- Conventions-writer: "Prefer updating existing docs in place rather than rewriting them from scratch."
- Legacy-doc-consolidator: "Do not overwrite canonical docs wholesale when incremental updates are sufficient."

### Observed: Effort Policy

The orchestrator begins by attempting to run `/effort max` before any other step. This is a model-level instruction asking the LLM runtime to apply maximum reasoning effort — not an optimization of workflow steps. If the command is unavailable, the orchestrator continues with the same step sequence but without the effort-level guarantee.

## GFM Formatting Requirements

### Required: Markdown Structure for Generated Docs

All generated documentation files must follow this structure:

- GitHub-Flavored Markdown (GFM)
- UTF-8 encoding
- H1 (`#`) for the document title
- H2 (`##`) for major sections
- H3 (`###`) for subsections
- File ends with `## Assumptions`

### Observed: Table Usage

Tables are used extensively throughout the orchestrator and agent prompts for structured information (tool permissions, step mappings, mode comparisons). Generated docs follow this pattern in practice.

## Assumptions

- The difference between `allowed-tools` (commands) and `tools` (agents) is a Claude Code platform convention, not a project-level choice. If Claude Code changes this convention, the project would need to follow.
- The `model` key in command frontmatter is functional and causes the Claude Code runtime to route requests to that specific model. Subagents inherit the model or use Claude Code defaults.
- The commented-out `accepted-arguments` key in the orchestrator suggests arguments are handled via `$ARGUMENTS` interpolation by the Claude Code runtime rather than through explicit frontmatter declaration.
- The fan-in summary structure described in this document is a prompt-level requirement. Whether the Claude Code runtime enforces or validates fan-in summaries is unknown -- compliance depends on the agent's adherence to its instructions.
