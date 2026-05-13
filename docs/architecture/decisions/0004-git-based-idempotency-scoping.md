# 0004. Git-Based Idempotency for Re-Run Scoping

Date: 2026-05-07

## Status

Accepted

## Context and Problem Statement

The documentation generation workflow is designed to be re-run as the codebase evolves. On subsequent runs, re-executing all steps when only a subset of source files have changed is wasteful and risks overwriting manual edits to documentation. The system needs a mechanism to determine which pipeline steps require re-execution and to detect uncommitted manual changes in the output directory before overwriting them.

## Considered Options

- Git-based change detection using commit history and diffs
- File checksum comparison (hash each source file against a stored manifest)
- Filesystem timestamp comparison (mtime-based staleness detection)
- No idempotency -- always re-run all steps

## Decision Outcome

Chosen option: **Git-based change detection**, because the target projects are expected to be git repositories, and git provides both commit-level change tracking and working-tree diff detection without requiring the workflow to maintain its own state files.

STEP 0.4 in the orchestrator implements two checks. Check 1 (step scoping) runs `git log -1 --format="%H" -- "$OUTPUT_ROOT"/` to find the last commit that touched the docs folder, then `git diff "$LAST_SHA" HEAD --name-only` to identify which source files changed since that commit. These commands are executed by the orchestrator via the `Bash` tool with `OUTPUT_ROOT` bound to the resolved output path (default: `docs`). To reproduce manually, substitute `docs` for `$OUTPUT_ROOT`. The changed paths are mapped to pipeline steps: source code changes trigger STEPS 1-5 + 8; docs-only changes trigger STEP 8 only; no changes prompt the user to force re-run or exit. Check 2 (manual edit detection) runs `git diff HEAD -- "$OUTPUT_ROOT"/` to detect uncommitted changes in the output directory, warning the user that manual edits may not be preserved.

The system degrades gracefully when git is unavailable: both checks are skipped and all steps run unconditionally. The `mode=force` option explicitly bypasses STEP 0.4 for situations where docs are out of sync with git.

### Consequences

- Good: No additional state files or manifests to maintain. Idempotency scoping leverages the existing git history that developers already maintain.
- Good: Manual edit detection via `git diff HEAD` catches uncommitted doc changes before overwriting, supporting a human-in-the-loop safety check.
- Good: Graceful degradation when git is unavailable means the workflow still functions in non-git environments, just without optimization.
- Bad: Relies on developers committing generated docs to git. If a previous run's output was never committed, `git log` returns no SHA and all steps re-run (see [`docs/specs/00-overview.md` § Force Mode](../../specs/00-overview.md#force-mode) for the full `mode=force` behavior).
- Bad: The granularity is at the file-path level, not semantic content. A cosmetic change to a source file triggers full re-execution of its associated pipeline steps.
