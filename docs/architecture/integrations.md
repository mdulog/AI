# Integrations

## Overview

`generate-knowledge-base` is a Claude Code skill, not a compiled application with traditional runtime dependencies. It has no databases, message queues, or network services. Its integrations are limited to the execution environment (Claude Code), the local filesystem, and optionally Git.

## Claude Code Runtime

**Role:** Execution environment and tool provider.

The entire workflow runs within the Claude Code runtime. The runtime provides the tool set that both the orchestrator and subagents use:

| Tool | Purpose | Used by |
|---|---|---|
| `Read` | Read files from the local filesystem | All components |
| `Write` | Write files to the local filesystem | Orchestrator + write agents |
| `Bash` | Execute shell commands | All components |
| `Agent` | Invoke subagent threads | Orchestrator only |
| `Glob` | Pattern-based file discovery | Most subagents |
| `Grep` | Text search within files | Most subagents |

The orchestrator declares `model: claude-opus-4-6` in its YAML frontmatter, directing the Claude Code runtime to use that specific model for the orchestrator thread.

### Deployment Mechanism

Claude Code discovers the orchestrator by its presence in `.claude/commands/` and subagents by their presence in `.claude/agents/` within the target project. The skill ships as source files in `generate-knowledge-base/` and must be copied into these locations before use:

```
.claude/commands/generate-knowledge-base.md   <-- orchestrator
.claude/agents/spec-brainstormer.md            <-- subagents (6 files)
.claude/agents/spec-writer.md
.claude/agents/conventions-writer.md
.claude/agents/legacy-doc-consolidator.md
.claude/agents/adr-writer.md
.claude/agents/spec-auditor.md
```

### Pre-approved Permissions

The repository includes a `.claude/settings.local.json` that pre-approves two specific Bash commands for agent deployment:

```json
{
  "permissions": {
    "allow": [
      "Bash(mkdir -p .claude/agents)",
      "Bash(cp generate-knowledge-base/Agents/spec-brainstormer.md generate-knowledge-base/Agents/spec-writer.md generate-knowledge-base/Agents/conventions-writer.md generate-knowledge-base/Agents/legacy-doc-consolidator.md generate-knowledge-base/Agents/adr-writer.md generate-knowledge-base/Agents/spec-auditor.md .claude/agents/)"
    ]
  }
}
```

Note: the `cp` permission grants an exact literal command — not a glob or wildcard. Only this specific invocation is pre-approved.

This allows the deployment commands to run without per-invocation user approval.

## Git

**Role:** Idempotency scoping, legacy migration, and change detection.

**Status:** Optional. The workflow degrades gracefully when git is unavailable or the project is not a git repository.

### Usage Points

| Step | Git operation | Purpose |
|---|---|---|
| STEP 0.4 | `git log -1 --format="%H" -- "$OUTPUT_ROOT"/` | Find the last commit that touched the docs folder |
| STEP 0.4 | `git diff "$LAST_SHA" HEAD --name-only` | Determine which source files changed since the last docs commit |
| STEP 0.4 | `git diff HEAD -- "$OUTPUT_ROOT"/` | Detect uncommitted manual edits in the docs folder |
| STEP 0.5 | `git mv` | Move legacy doc files while preserving git history |
| STEP 5 | `git pull` | Sync local ADR folder with remote before numbering (prevents concurrent-run collisions). **Orchestrator action** — performed before delegating to `adr-writer`. Subagents do not have network access. |

### Degraded Mode

When git is unavailable:
- STEP 0.4 idempotency checks are skipped entirely; all steps run unconditionally.
- STEP 0.5 falls back to filesystem moves instead of `git mv`, losing history preservation.
- STEP 5 skips the `git pull` sync; concurrent-run ADR collisions become possible.

The orchestrator logs a warning when git is unavailable but does not stop execution.

## Local Filesystem

**Role:** Primary input (codebase files) and output (generated documentation).

The workflow reads the target project's codebase from the local filesystem and writes all generated documentation to `{OUTPUT_ROOT}/` (default: `docs/`). The output folder structure is created in STEP 0 if it does not already exist, with `.gitkeep` files in empty directories.

### Output Paths

See [architecture/overview.md](overview.md) for the complete output taxonomy.

## Superpowers Plugin (Optional)

**Role:** Extended analysis and documentation capabilities.

The orchestrator declares optional integration with a Superpowers plugin. Detection is orchestrator-side at runtime, checking for `.claude/skills/superpowers` or Superpowers entries in `.claude/settings.json`. No subagent file references Superpowers directly — the integration is described only in the orchestrator's instructions.

When available, specific subagents may use Superpowers skills for their designated role:
- `spec-brainstormer` — analysis or exploration skills
- `spec-writer` — documentation or design skills
- `conventions-writer` — coding-style or refactoring skills
- `legacy-doc-consolidator` — summarization or classification skills
- `adr-writer` — ADR or architecture skills
- `spec-auditor` — review skills

This integration is purely opportunistic:
- No step depends on Superpowers being available.
- Agent behavior is identical whether or not Superpowers is present.
- Superpowers skills must respect the orchestrator's safety rules (no blind overwrites, no legacy file deletion, no invented facts).

## What This Project Does Not Integrate With

For clarity, this skill has no:

- **Databases or data stores** -- it reads source files and writes markdown; there is no persistence layer.
- **Network services or APIs** -- all interaction is via local filesystem and the Claude Code runtime.
- **Message queues or event buses** -- inter-agent communication is handled by the orchestrator passing inline context.
- **CI/CD pipelines** -- no CI/CD integration is currently defined; the skill is designed for manual invocation via `/generate-knowledge-base`.
- **Authentication or authorization systems** -- execution relies on the Claude Code session's existing permissions.
- **Container or cloud infrastructure** -- runs locally on the user's machine within Claude Code.

## Assumptions

- The Claude Code runtime enforces the tool permissions declared in YAML frontmatter. An agent declaring `tools: [Read, Bash, Glob, Grep]` cannot invoke the `Write` tool even if it attempts to.
- The `model: claude-opus-4-6` declaration is functional and causes the Claude Code runtime to route the orchestrator's requests to that specific model. Without this declaration, a different default model might be used.
- Git operations in the workflow assume a standard git setup (remote tracking branches, typical commit history). Non-standard configurations (shallow clones, detached HEAD states, submodules) may cause unexpected behavior in STEP 0.4 or STEP 0.5.
- The Superpowers plugin integration is described only in the orchestrator file. No subagent file references Superpowers directly, suggesting the orchestrator's description serves as documentation of a future or optional capability rather than a currently exercised integration.
