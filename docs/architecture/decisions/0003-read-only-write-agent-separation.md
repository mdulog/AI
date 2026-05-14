# 0003. Read-Only and Write Agent Separation via Tool Permissions

Date: 2026-05-07

## Status

Accepted

## Context and Problem Statement

The pipeline includes agents with fundamentally different roles: some perform analysis and review (spec-brainstormer in STEP 1, spec-auditor in STEP 6), while others generate or modify documentation files (spec-writer, conventions-writer, adr-writer, legacy-doc-consolidator). The system needs a mechanism to enforce that analysis agents cannot accidentally modify files and that the boundary between read and write operations is structurally guaranteed rather than relying on prompt compliance alone.

## Considered Options

- Enforce read-only behavior through natural language instructions in the agent prompt only
- Enforce read-only behavior through tool permission scoping in YAML frontmatter, with the Claude Code runtime as the enforcement mechanism
- Use a shared agent definition with a runtime mode flag (read vs. write) passed per invocation

## Decision Outcome

Chosen option: **Enforce read-only behavior through tool permission scoping in YAML frontmatter**, because the Claude Code runtime enforces the `tools` declaration in each agent's frontmatter, preventing tool access regardless of what the agent's prompt instructs.

Read-only agents declare `tools: [Read, Bash, Glob, Grep, Skill]` -- notably excluding `Write`. This applies to `spec-brainstormer.md` and `spec-auditor.md`. Write-capable agents include `Write` in their tool list: `spec-writer.md` (`tools: [Read, Write, Bash, Grep, Skill]`), `conventions-writer.md` (`tools: [Read, Write, Bash, Glob, Grep, Skill]`), `adr-writer.md` (`tools: [Read, Write, Bash, Glob, Skill]`), and `legacy-doc-consolidator.md` (`tools: [Read, Write, Bash, Glob, Grep, Skill]`). Additionally, only the orchestrator declares the `Agent` tool (`allowed-tools: [Read, Write, Bash, Agent]`), which prevents any subagent from spawning other agents and enforces the supervisor-led pattern.

`Skill` is granted to every subagent so they can invoke optional Superpowers skills when the plugin is installed (orchestrator § Superpowers usage). It is orthogonal to the read/write split codified here: skills can only orchestrate tools the agent already holds, so a subagent without `Write` still cannot write files via a skill.

Note: `spec-writer` is the only write-capable agent without `Glob`. It uses `Bash` and `Grep` for file discovery — consistent with its verify-before-writing mandate — while all other write agents include `Glob` for broader pattern-based file listing.

### Consequences

- Good: The read-only constraint is enforced at the runtime level, not just the prompt level. A read-only agent cannot write files even if prompt injection or instruction drift occurs.
- Good: The audit step (STEP 6) is structurally prevented from modifying the docs it reviews, ensuring the human-in-the-loop step (STEP 7) remains meaningful.
- Good: Tool permissions are visible in each agent's frontmatter, making the security boundary auditable by reading the first few lines of each file.
- Bad: Tool permissions are static per agent definition. If a future workflow step requires a read-only agent to optionally write (e.g., the auditor producing a report file), the agent definition must be modified or a new agent created. The `spec-auditor` was specifically designed to return its correction list as inline output — not a file artifact — to preserve its read-only status and avoid producing a file that could be mistaken for an authoritative correction commitment.
- Bad: The assumption that the Claude Code runtime enforces these declarations is not independently verified by the system. If the runtime fails to enforce tool restrictions, the safety boundary is silently absent.
