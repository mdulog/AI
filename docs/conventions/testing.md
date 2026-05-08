# Testing Conventions

## Overview

This project has no automated test suite. It is a pure-markdown Claude Code skill consisting of YAML frontmatter and structured prompt definitions. There is no compiled code, no test framework, no test runner, and no CI/CD pipeline.

## Validation Strategy

Quality assurance is handled through two mechanisms built into the workflow itself rather than through external tests:

### Spec Auditor Agent (STEP 6)

The `spec-auditor` subagent acts as the primary validation mechanism. In `mode=full`, it reviews every generated document against the real codebase and produces a prioritized correction list.

For each file, the auditor checks:

1. Contradictions with the real code
2. Assumptions that cannot be verified
3. Missing information that should be present
4. Sections that are vague or overly generic
5. Content that belongs in a different doc category

Issues are categorized as High, Medium, or Low priority. The auditor never modifies files -- it only reports.

### Human-in-the-Loop Review (STEP 7)

After the audit, the orchestrator presents all High and Medium priority corrections to the user for review. No corrections are applied until the user explicitly confirms which ones to proceed with. This is the only step in the workflow that gates on user approval before modifying files.

For the architectural mechanics of re-run scoping, see [architecture/overview.md — Idempotency](../architecture/overview.md).

## Manual Validation Procedures

When modifying agent prompt files, validate changes by deploying the modified files to a test project and running the affected step:

1. **Deploy modified agents** to a real project's `.claude/agents/` using the standard `cp` command.
2. **Exercise the relevant step** by running `/generate-knowledge-base` in the target project. Use `mode=light` for quick feedback on STEPS 1-4 and 8; use `mode=full` to also test STEPS 0.5, 0.6, 5, 6, and 7.
3. **Key scenario pairs to test**:
   - First run (empty `docs/`) vs. re-run (populated `docs/`) — verifies incremental update behavior
   - With git available vs. without git — verifies degraded mode
   - `mode=full` vs. `mode=light` vs. `mode=force` — verifies step skipping logic
4. **Expected observable outputs** per agent:
   - `spec-brainstormer`: returns a structured report in conversation context, creates no files
   - `spec-writer`: creates or updates architecture/spec markdown files under `docs/`
   - `conventions-writer`: creates or updates convention markdown files under `docs/conventions/`
   - `adr-writer`: creates numbered MADR files under `docs/architecture/decisions/`
   - `spec-auditor`: returns a prioritized issue list in conversation context, creates no files
   - `legacy-doc-consolidator`: updates canonical docs, returns consolidation report, preserves legacy files

## Why No Automated Tests

The "code" in this project is natural-language prompts interpreted by an LLM at runtime. Traditional unit tests, integration tests, and assertion-based testing do not apply because:

- There are no functions to call or return values to assert against.
- Prompt behavior depends on the LLM's interpretation, which is non-deterministic.
- The output is prose (markdown documents), not structured data with fixed schemas.

The spec-auditor agent is the project's functional equivalent of a test suite -- it performs evidence-based validation of generated output against source-of-truth code.

## Assumptions

- The spec-auditor agent's effectiveness as a validation mechanism depends on the quality of the underlying model and the specificity of its audit prompts. There is no way to guarantee audit coverage or consistency across runs.
- If the project evolves to include compiled code (e.g., a CLI wrapper, a test harness for prompt evaluation), a conventional test suite should be introduced at that point.
- The `mode=light` execution mode skips the audit step entirely, meaning light-mode runs have no automated validation beyond the human reviewing the output.
