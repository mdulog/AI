# 0002. Supervisor-Led Sequential Orchestration

Date: 2026-05-07

## Status

Accepted

## Context and Problem Statement

The system must coordinate six specialized subagents through an 11-step documentation generation pipeline (STEP 0 through STEP 8, including intermediate steps 0.4, 0.5, and 0.6). Steps have data dependencies: the brainstorm report from STEP 1 feeds into STEPS 2, 3, and 4; architecture docs from STEP 2 feed into STEP 5; and all generated docs feed into STEP 6's audit. The execution model must ensure correct ordering, prevent data races, and support three execution modes (full, light, force).

## Considered Options

- Supervisor-led sequential orchestration with a single orchestrator controlling all flow
- DAG-based orchestration where steps declare their dependencies and a scheduler resolves execution order
- Event-driven orchestration where agents publish completion events and downstream agents subscribe
- Fully parallel execution with locking mechanisms for shared resources

## Decision Outcome

Chosen option: **Supervisor-led sequential orchestration**, because the pipeline has strict sequential dependencies (brainstorm before writing, writing before audit, audit before corrections) and only one component -- the orchestrator -- holds the `Agent` tool, making it the sole entity capable of invoking subagents.

The orchestrator runs steps in a fixed order defined in `generate-knowledge-base.md`. Subagents never invoke other subagents and never communicate with each other directly. Inter-step data flow is handled by the orchestrator passing the brainstorm report as inline context in `Agent` tool invocations -- no intermediate files, message queues, or shared state. The orchestrator manages execution mode logic, determining which steps to skip based on the mode parameter and git-diff scoping results from STEP 0.4.

### Consequences

- Good: Simple mental model -- the orchestrator file reads top-to-bottom as the execution sequence. No hidden scheduling logic or implicit dependency resolution.
- Good: No race conditions between agents. Each step completes before the next begins, and the orchestrator passes context explicitly.
- Good: Execution modes (full, light, force) are straightforward conditional skips rather than complex graph modifications.
- Bad: No concurrent execution across steps, even when steps could theoretically run in parallel (e.g., STEP 3 conventions-writer does not depend on STEP 2's brainstorm report inputs, but it does receive "existing docs under OUTPUT_ROOT" as an additional input — meaning STEP 3 benefits from STEP 2's written output even without a direct dependency, and parallel execution would give it inconsistent access to architecture docs being written concurrently).
- Bad: The orchestrator is a single point of failure. If it loses context or encounters an error mid-pipeline, there is no checkpoint or resume mechanism. Starting over from STEP 0 is required. This is an accepted trade-off for simplicity.
