# 0007. Mode-Based Execution Control with a Force Escape Hatch

Date: 2026-05-08

## Status

Accepted

## Context and Problem Statement

The skill is invoked in three distinct situations that share most steps but differ in which expensive or semi-destructive steps should run:

1. **First-time onboarding** of a project that has no docs — every step is needed.
2. **Quick refresh** during active development — legacy migration, ADRs, audit, and corrections add cost and noise that aren't justified for routine re-runs.
3. **Out-of-band recovery** — the docs folder has drifted from git history (a previous run's output was never committed), so the git-diff-based idempotency scoping in STEP 0.4 produces wrong answers and must be bypassed.

A single fixed pipeline cannot serve all three. STEPS 0.5 (legacy migration), 0.6 (legacy consolidation), 5 (ADR generation), 6 (audit), and 7 (corrections) are heavy, occasionally destructive, and not all needed every run. STEP 0.4 (git-diff scoping) is a correctness gate in the normal case but is actively wrong in the recovery case. Both differences must be expressible without forking the orchestrator.

## Considered Options

- **Single fixed pipeline** — every run executes every step; users wait through unnecessary work or skip the skill entirely.
- **Per-step boolean flags** — separate `--skip-adrs`, `--skip-audit`, `--force`, etc. flags composed by the user.
- **Mode-based gating** — three named modes (`full`, `light`, `force`) that each correspond to a coherent intent, with the per-step skip condition intersected with the mode's permitted set (more restrictive wins).
- **External config file** — a `.knowledge-base.yml` declaring which steps to run.

## Decision Outcome

Chosen option: **Mode-based gating with a `force` escape hatch**, because the three named modes map cleanly to the three real use cases and avoid the combinatorial complexity of per-step flags. The mode is a single argument, the intent is named, and the orchestrator's step gates are simple conditionals rather than a flag-composition matrix.

The orchestrator (§ Execution mode) defines three modes:

| Mode | Behavior |
|---|---|
| `full` (default) | Runs the complete workflow: STEP 0, 0.4, 0.5, 0.6, 1, 2, 3, 4, 5, 6, 7, 8. |
| `light` | Skips STEP 0.5, 0.6, 5, 6, 7. Always runs 0, 0.4, 1, 2, 3, 4, 8. |
| `force` | Identical to `full` but bypasses STEP 0.4 git-diff scoping and uncommitted-edit confirmation. |

Two design rules govern mode interaction with per-step gates:

- **Each step is individually marked with its skip condition** — those markers are the authoritative source. The mode parameter is the more restrictive intersection rule, not a substitute for per-step gates.
- **`force` is not a third mode in the "what runs" axis** — it is `full` plus a STEP 0.4 bypass. This keeps the "what runs" decision orthogonal to the "is git-diff scoping trustworthy right now" decision.

The `force` escape hatch exists specifically because git-based idempotency (ADR 0004) is correct in the common case but actively wrong when the docs folder is out of sync with git history. Without `force`, recovering from an aborted previous run would require committing partial output just to satisfy the scoping check, which would be backwards.

### Consequences

- Good: Users learn three names, not a flag matrix. The intent of each mode is self-documenting (`full` = everything, `light` = quick, `force` = recovery).
- Good: Step gates remain simple `if mode == X` checks rather than flag-composition expressions. New steps slot into the existing matrix by declaring which modes they belong to.
- Good: `force` cleanly separates the orthogonal concern of "should we trust git scoping?" from "which steps should run?", preventing the two from being coupled in user-visible flags.
- Good: The `light` mode answers a real recurring need — during active development, contributors want refreshed architecture/conventions/specs without re-running ADR deduplication or the auditor on every iteration.
- Bad: Three modes is a compromise. A user who wants `light` plus ADRs (but not audit) cannot express that today; they must run `full` and accept the audit cost. The system traded expressivity for simplicity.
- Bad: The `force` mode disables the manual-edit detection check from STEP 0.4, meaning uncommitted doc edits can be silently overwritten when recovering from drift. The naming (`force`) signals risk, but the loss of the safety check is implicit rather than spelled out at the dispatch site.
- Bad: Modes are documented in four places: the orchestrator's `# accepted-arguments` frontmatter comment, the orchestrator's § Execution mode, `architecture/overview.md`, and the skill's user-facing README. Drift between these surfaces is possible if a future mode is added without updating all four.
- Neutral: The mode parameter is the only execution-control argument the slash command accepts (besides `output-root-folder`). Adding a fourth mode is cheap; refactoring to per-step flags later would be a breaking change to the public surface.

## Assumptions

- The three observed use cases (onboarding, refresh, recovery) are the dominant ones. If a fourth distinct workflow emerges (e.g. "audit only"), it would justify either a fourth mode or a refactor to per-step flags — but neither is needed today.
- Users can be trusted to choose `force` only when they understand the docs-folder drift situation. The orchestrator does not attempt to auto-detect drift and silently switch modes; that remains a user decision.
- Skipping the audit (STEP 6) and corrections (STEP 7) in `light` mode is acceptable because those steps are quality-improving rather than correctness-critical. A `light` run produces docs; a `full` run produces docs that have been cross-checked.
- The mode parameter is not validated against a typo allow-list at the orchestrator level — a misspelled mode would currently be treated as the default. Accepted as low-risk because the failure mode (running `full` instead of `light`) is conservative.
