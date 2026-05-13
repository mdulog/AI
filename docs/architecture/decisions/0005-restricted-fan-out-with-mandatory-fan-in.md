# 0005. Restricted Fan-Out with Mandatory Fan-In for Safe Parallelism

Date: 2026-05-07

## Status

Accepted

## Context and Problem Statement

Individual pipeline steps can involve work that is naturally parallelizable -- scanning independent directories during brainstorm, auditing independent documentation files, or classifying batches of legacy documents. However, unrestricted parallel execution risks write conflicts (multiple agents writing to the same file), inconsistent state (partial results consumed by downstream steps), and numbering collisions (concurrent ADR creation). The system needs a parallelism policy that enables performance gains where safe while preventing data corruption.

## Considered Options

- Unrestricted parallel execution with file-level locking
- Strictly sequential execution within every step (no intra-step parallelism)
- Restricted fan-out with mandatory fan-in: parallel work allowed only under explicit safety conditions, with a required merge step before downstream work continues

## Decision Outcome

Chosen option: **Restricted fan-out with mandatory fan-in**, because it permits performance-beneficial parallelism within steps while maintaining the deterministic, conflict-free guarantees required by a documentation generation workflow.

The orchestrator's "Safe parallelism policy" section defines three conditions that must all be true for fan-out to be permitted: (1) each parallel task works on independent inputs, (2) each parallel task writes to a distinct target file or returns read-only analysis, and (3) the step defines an explicit fan-in summary before downstream work continues. The fan-in summary must list each subtask, record success/failure/skipped status, merge non-conflicting findings, and surface conflicts explicitly.

The policy explicitly prohibits parallelizing: writes to the same markdown file, CLAUDE.md migration or finalization, ADR numbering and creation (unless numbering ownership is centralized), and correction application across overlapping target files. The policy is defined in the orchestrator's § Safe parallelism policy and restated in three relevant subagent definitions — spec-brainstormer, legacy-doc-consolidator, and spec-auditor — each adapting the wording to their operational context.

### Consequences

- Good: Enables meaningful parallelism for read-heavy operations (repo scanning, per-file audits, legacy doc classification) without risking write conflicts.
- Good: The mandatory fan-in summary creates an auditable merge point, making it possible to detect and surface conflicts rather than silently resolving them.
- Good: The explicit prohibition list (same-file writes, CLAUDE.md, ADR numbering) prevents the highest-risk parallel operations from being attempted.
- Bad: The policy is enforced by natural language instructions in agent prompts, not by a runtime mechanism. An agent that ignores fan-in requirements has no technical barrier preventing it from producing inconsistent results.
- Bad: There is no post-hoc mechanism to verify whether an agent actually followed the fan-in requirement during its execution. The orchestrator's fan-in summary check is itself a natural-language instruction — a non-compliant agent could skip it without detection.
- Bad: The conditions for safe fan-out must be evaluated by the agent at runtime, introducing ambiguity about whether a particular set of tasks truly meets all three criteria.
